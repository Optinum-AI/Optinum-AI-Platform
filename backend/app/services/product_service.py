import json

from ..agents import orchestrator
from ..security import new_id, now_iso
from . import connection_service


async def create(conn, user_id: str, name: str, description: str, preset: str | None):
    pid = new_id("prd")
    now = now_iso()
    conn.execute(
        "INSERT INTO products (id, user_id, name, description, preset, created_at) VALUES (?,?,?,?,?,?)",
        (pid, user_id, name, description, preset, now),
    )
    conn.commit()
    product = dict(conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone())
    platforms = connection_service.active_platforms(conn, user_id)
    graph, provider = await orchestrator.generate_graph(
        {"name": product["name"], "description": product["description"]}, platforms
    )
    sid = new_id("str")
    conn.execute(
        "INSERT INTO strategies (id, product_id, user_id, graph_json, version, created_at, updated_at) VALUES (?,?,?,?,1,?,?)",
        (sid, pid, user_id, json.dumps(graph), now, now),
    )
    conn.commit()
    strategy = dict(conn.execute("SELECT * FROM strategies WHERE id=?", (sid,)).fetchone())
    return product, strategy, provider
