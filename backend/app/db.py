import sqlite3
from pathlib import Path

from . import config


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    schema = (Path(__file__).parent / "schema.sql").read_text()
    conn = connect()
    conn.executescript(schema)
    check = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='connections'"
    ).fetchone()
    if check and "discord" not in (check["sql"] or ""):
        conn.execute("ALTER TABLE connections RENAME TO connections_legacy")
        conn.executescript(schema)
        conn.execute(
            "INSERT INTO connections (id,user_id,platform,handle,access_token,status,mode,enabled,refresh_token,external_account_id,connected_at,expires_at,last_sync_at) "
            "SELECT id,user_id,platform,handle,access_token,status,mode,enabled,refresh_token,external_account_id,connected_at,expires_at,last_sync_at "
            "FROM connections_legacy"
        )
        conn.execute("DROP TABLE connections_legacy")
    for stmt in (
        "ALTER TABLE connections ADD COLUMN mode TEXT DEFAULT 'sim'",
        "ALTER TABLE connections ADD COLUMN enabled INTEGER DEFAULT 1",
        "ALTER TABLE connections ADD COLUMN refresh_token TEXT",
        "ALTER TABLE connections ADD COLUMN external_account_id TEXT",
        "ALTER TABLE posts ADD COLUMN external_id TEXT",
        "ALTER TABLE posts ADD COLUMN error TEXT",
    ):
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
