import secrets
from datetime import datetime, timedelta, timezone

from ..security import new_id, now_iso
from ..social import creds

TOKEN_TTL_MINUTES = 60


def _with_state(row: dict) -> dict:
    row = dict(row)
    if row["status"] == "active" and row["expires_at"] < now_iso():
        row["status"] = "expired"
    row["enabled"] = bool(row.get("enabled", 1))
    return row


def list_for_user(conn, user_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM connections WHERE user_id = ? ORDER BY platform", (user_id,)
    ).fetchall()
    return [_with_state(r) for r in rows]


def active_platforms(conn, user_id: str) -> list[str]:
    return [c["platform"] for c in list_for_user(conn, user_id) if c["status"] == "active"]


def link(conn, user_id: str, platform: str, handle: str) -> dict:
    now = now_iso()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)).isoformat()
    is_discord = platform == "discord" and creds.configured("discord")
    token = creds.get("discord")[0] if is_discord else secrets.token_hex(24)
    mode = "real" if is_discord else "sim"
    existing = conn.execute(
        "SELECT id FROM connections WHERE user_id = ? AND platform = ?", (user_id, platform)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE connections SET handle=?, access_token=?, status='active', mode=?, enabled=1, connected_at=?, expires_at=?, last_sync_at=? WHERE id=?",
            (handle, token, mode, now, expires, now, existing["id"]),
        )
        conn.commit()
        return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (existing["id"],)).fetchone()))
    cid = new_id("con")
    conn.execute(
        "INSERT INTO connections (id, user_id, platform, handle, access_token, status, mode, enabled, connected_at, expires_at, last_sync_at) VALUES (?,?,?,?,?,'active',?,1,?,?,?)",
        (cid, user_id, platform, handle, token, mode, now, expires, now),
    )
    conn.commit()
    return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (cid,)).fetchone()))


def link_real(conn, user_id: str, platform: str, tokens: dict, handle: str) -> dict:
    now = now_iso()
    expires = (
        datetime.now(timezone.utc) + timedelta(days=30)
    ).isoformat()
    existing = conn.execute(
        "SELECT id FROM connections WHERE user_id = ? AND platform = ?", (user_id, platform)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE connections SET handle=?, access_token=?, refresh_token=?, status='active', mode='real', enabled=1, connected_at=?, expires_at=?, last_sync_at=? WHERE id=?",
            (handle, tokens["access_token"], tokens.get("refresh_token"), now, expires, now, existing["id"]),
        )
        conn.commit()
        return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (existing["id"],)).fetchone()))
    cid = new_id("con")
    conn.execute(
        "INSERT INTO connections (id, user_id, platform, handle, access_token, refresh_token, status, mode, enabled, connected_at, expires_at, last_sync_at) VALUES (?,?,?,?,?,?, 'active','real',1,?,?,?)",
        (cid, user_id, platform, handle, tokens["access_token"], tokens.get("refresh_token"), now, expires, now),
    )
    conn.commit()
    return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (cid,)).fetchone()))


def link_browser(conn, user_id: str, platform: str, handle: str) -> dict:
    now = now_iso()
    expires = (
        datetime.now(timezone.utc) + timedelta(days=30)
    ).isoformat()
    existing = conn.execute(
        "SELECT id FROM connections WHERE user_id = ? AND platform = ?", (user_id, platform)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE connections SET handle=?, access_token=?, refresh_token='browser', status='active', mode='browser', enabled=1, connected_at=?, expires_at=?, last_sync_at=? WHERE id=?",
            (handle, user_id, now, expires, now, existing["id"]),
        )
        conn.commit()
        return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (existing["id"],)).fetchone()))
    cid = new_id("con")
    conn.execute(
        "INSERT INTO connections (id, user_id, platform, handle, access_token, refresh_token, status, mode, enabled, connected_at, expires_at, last_sync_at) VALUES (?,?,?,?,?,'browser','active','browser',1,?,?,?)",
        (cid, user_id, platform, handle, user_id, now, expires, now),
    )
    conn.commit()
    return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (cid,)).fetchone()))



async def sync_metrics(conn, connection: dict) -> int:
    """Pull real metrics for published posts on a live connection. Returns rows updated."""
    from ..social.registry import get_adapter

    adapter = get_adapter(connection["platform"])
    if connection.get("mode") != "real" or adapter is None or not adapter.configured():
        return 0
    rows = conn.execute(
        "SELECT p.id, p.external_id FROM posts p WHERE p.connection_id=? AND p.external_id IS NOT NULL",
        (connection["id"],),
    ).fetchall()
    updated = 0
    for row in rows:
        try:
            m = await adapter.fetch_metrics(connection["access_token"], row["external_id"])
        except Exception:
            m = None
        if not m or sum(m.values()) == 0:
            continue
        conn.execute(
            "UPDATE metrics SET impressions=?, clicks=?, likes=?, comments=?, shares=? WHERE post_id=?",
            (m["impressions"], m.get("clicks", 0), m["likes"], m["comments"], m["shares"], row["id"]),
        )
        updated += 1
    if updated:
        conn.execute("UPDATE connections SET last_sync_at=? WHERE id=?", (now_iso(), connection["id"]))
        conn.commit()
    return updated


def resync(conn, connection_id: str, user_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM connections WHERE id=? AND user_id=?", (connection_id, user_id)
    ).fetchone()
    if not row:
        return None
    now = now_iso()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)).isoformat()
    conn.execute(
        "UPDATE connections SET status='active', expires_at=?, last_sync_at=?, access_token=? WHERE id=?",
        (expires, now, secrets.token_hex(24), connection_id),
    )
    conn.commit()
    return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (connection_id,)).fetchone()))


def toggle_enabled(conn, connection_id: str, user_id: str, enabled: bool) -> dict | None:
    row = conn.execute(
        "SELECT * FROM connections WHERE id=? AND user_id=?", (connection_id, user_id)
    ).fetchone()
    if not row:
        return None
    conn.execute(
        "UPDATE connections SET enabled=?, last_sync_at=? WHERE id=?",
        (1 if enabled else 0, now_iso(), connection_id),
    )
    conn.commit()
    return _with_state(dict(conn.execute("SELECT * FROM connections WHERE id=?", (connection_id,)).fetchone()))


def disconnect(conn, connection_id: str, user_id: str) -> bool:
    cur = conn.execute("DELETE FROM connections WHERE id=? AND user_id=?", (connection_id, user_id))
    conn.commit()
    return cur.rowcount > 0
