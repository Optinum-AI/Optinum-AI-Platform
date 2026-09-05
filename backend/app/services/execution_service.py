import hashlib
import json
import random
import time
from datetime import datetime

from .. import db
from ..agents import graph_schema as gs
from ..agents import orchestrator
from ..llm.heuristic import PLATFORM_BASE_IMPRESSIONS
from ..security import new_id, now_iso
from ..social import registry as social_registry

NODE_PERSONA = {
    "goal": "strategist",
    "audience": "strategist",
    "experiment": "strategist",
    "content": "copywriter",
    "cadence": "scheduler",
    "channel": "copywriter+creative+scheduler",
}


def _seed(post_id: str) -> random.Random:
    return random.Random(hashlib.sha256(post_id.encode()).hexdigest())


def _simulate_metrics(conn, post_id: str, platform: str, scheduled_at: str):
    rng = _seed(post_id)
    base = PLATFORM_BASE_IMPRESSIONS.get(platform, 800)
    impressions = int(base * rng.uniform(0.7, 1.3))
    clicks = int(impressions * 0.015 * rng.uniform(0.5, 1.5))
    likes = int(impressions * 0.04 * rng.uniform(0.5, 1.5))
    comments = int(impressions * 0.006 * rng.uniform(0.5, 1.5))
    shares = int(impressions * 0.008 * rng.uniform(0.5, 1.5))
    resolved = 1 if rng.random() < 0.87 else 0
    try:
        hour = datetime.fromisoformat(scheduled_at).hour
    except Exception:
        hour = 9
    conn.execute(
        "INSERT INTO metrics (id, post_id, impressions, clicks, likes, comments, shares, resolved, hour_bucket, captured_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (new_id("met"), post_id, impressions, clicks, likes, comments, shares, resolved, f"{hour:02d}:00", now_iso()),
    )


async def run(exec_id: str, strategy: dict, user_id: str) -> None:
    conn = db.connect()
    try:
        await _run_inner(conn, exec_id, strategy, user_id)
    except Exception as exc:
        conn.execute(
            "UPDATE executions SET status='failed', finished_at=?, logs_json=? WHERE id=?",
            (now_iso(), json.dumps([{"node_id": "fleet", "type": "error", "persona": "system",
                                     "provider": "none", "ms": 0, "excerpt": str(exc)}]), exec_id),
        )
        conn.commit()
    finally:
        conn.close()


async def _run_inner(conn, exec_id: str, strategy: dict, user_id: str) -> None:
    graph = json.loads(strategy["graph_json"])
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    by_id = {n["id"]: n for n in nodes}
    product_row = conn.execute("SELECT * FROM products WHERE id=?", (strategy["product_id"],)).fetchone()
    product = {"name": product_row["name"], "description": product_row["description"]}

    logs = []
    t0 = time.time()
    notes, notes_provider = await orchestrator.generate_notes(product, graph)
    logs.append({
        "node_id": "fleet", "type": "notes", "persona": "strategist",
        "provider": notes_provider, "ms": int((time.time() - t0) * 1000),
        "excerpt": "; ".join(notes[:3]),
    })
    conn.execute("UPDATE executions SET logs_json=? WHERE id=?", (json.dumps(logs), exec_id))
    conn.commit()

    order = gs.topo_sort(nodes, edges)
    for nid in order:
        node = by_id[nid]
        ctx = gs.context_for(nid, nodes, edges)
        t0 = time.time()
        if node["type"] == "channel":
            params = {}
            for key in ("goal", "audience", "content", "cadence", "channel", "experiment"):
                params.update(ctx.get(key, {}))
            n = max(2, min(4, int(params.get("posts_per_week", 3))))
            posts_texts, posts_provider = await orchestrator.generate_posts(node, ctx, product, n)
            asset_notes, _ = await orchestrator.generate_creative(node, ctx, product, len(posts_texts))
            slots, _ = await orchestrator.generate_schedule(node, ctx, len(posts_texts))
            platform = params.get("platform", node.get("params", {}).get("platform", "linkedin"))
            conn_row = conn.execute(
                "SELECT id, mode, access_token FROM connections WHERE user_id=? AND platform=? AND status='active' AND enabled=1",
                (user_id, platform),
            ).fetchone()
            adapter = social_registry.get_adapter(platform)
            live = bool(conn_row and conn_row["mode"] in ("real", "browser") and adapter and adapter.configured())
            published = failed = 0
            for i, text in enumerate(posts_texts):
                post_id = new_id("pst")
                scheduled_at = slots[i % len(slots)] if slots else now_iso()
                external_id = None
                if live:
                    error = None
                    try:
                        external_id = await adapter.publish(conn_row["access_token"], text)
                        status = "published"
                        published += 1
                    except Exception as exc:
                        error = str(exc)
                        status = "auth_required" if "Authentication required" in error else "publish_failed"
                        failed += 1
                else:
                    error = None
                    status = "published_sim"
                conn.execute(
                    "INSERT INTO posts (id, execution_id, connection_id, platform, content_text, asset_notes, scheduled_at, status, external_id, error) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (post_id, exec_id, conn_row["id"] if conn_row else None, platform, text,
                     asset_notes[i % len(asset_notes)] if asset_notes else "", scheduled_at, status, external_id, error),
                )
                if live:
                    m = None
                    if external_id:
                        try:
                            m = await adapter.fetch_metrics(conn_row["access_token"], external_id)
                        except Exception:
                            m = None
                    m = m if m and sum(m.values()) > 0 else {"impressions": 0, "clicks": 0, "likes": 0, "comments": 0, "shares": 0}
                    try:
                        hour = datetime.fromisoformat(scheduled_at).hour
                    except Exception:
                        hour = 9
                    conn.execute(
                        "INSERT INTO metrics (id, post_id, impressions, clicks, likes, comments, shares, resolved, hour_bucket, captured_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (new_id("met"), post_id, m["impressions"], m.get("clicks", 0), m["likes"],
                         m["comments"], m["shares"], 0, f"{hour:02d}:00", now_iso()),
                    )
                else:
                    _simulate_metrics(conn, post_id, platform, scheduled_at)
            mode_label = "live" if live else "sim"
            logs.append({
                "node_id": nid, "type": "channel", "persona": NODE_PERSONA["channel"],
                "provider": posts_provider, "ms": int((time.time() - t0) * 1000),
                "excerpt": f"{platform} [{mode_label}]: {published} published, {failed} failed, {len(posts_texts) - published - failed} sim",
            })
        else:
            params = node.get("params", {})
            logs.append({
                "node_id": nid, "type": node["type"], "persona": NODE_PERSONA.get(node["type"], "strategist"),
                "provider": "pipeline", "ms": int((time.time() - t0) * 1000),
                "excerpt": ", ".join(f"{k}={v}" for k, v in params.items()),
            })
        conn.execute("UPDATE executions SET logs_json=? WHERE id=?", (json.dumps(logs), exec_id))
        conn.commit()
    conn.execute(
        "UPDATE executions SET status='completed', finished_at=?, logs_json=? WHERE id=?",
        (now_iso(), json.dumps(logs), exec_id),
    )
    conn.commit()
