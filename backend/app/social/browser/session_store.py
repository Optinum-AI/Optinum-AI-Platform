"""
Secure session storage for Playwright browser state.

Stores encrypted browser cookies/localStorage per user per platform.
Never stores user passwords — only session state captured after manual login.
"""

import base64
import hashlib
import json
import os
from pathlib import Path

from ... import config

# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

_SESSIONS_DIR = config.DATA_DIR / "sessions"


def _derive_key() -> bytes:
    """Derive a 32-byte Fernet key from the app SECRET_KEY."""
    raw = hashlib.sha256(config.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(raw)


def _encrypt(data: str) -> str:
    try:
        from cryptography.fernet import Fernet
        f = Fernet(_derive_key())
        return f.encrypt(data.encode()).decode()
    except Exception as exc:
        raise RuntimeError("Encrypted browser session storage is unavailable") from exc


def _decrypt(token: str) -> str:
    try:
        from cryptography.fernet import Fernet
        f = Fernet(_derive_key())
        return f.decrypt(token.encode()).decode()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _path_for(user_id: str, platform: str) -> Path:
    d = _SESSIONS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{platform}.enc"


def save_session(user_id: str, platform: str, state: dict) -> None:
    """Persist Playwright storage state (cookies + localStorage) encrypted."""
    uid = user_id or "default"
    path = _path_for(uid, platform)
    encrypted = _encrypt(json.dumps(state))
    path.write_text(encrypted)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def load_session(user_id: str, platform: str) -> dict | None:
    """
    Load saved session state with multi-tier fallback:
      1. Direct path for user_id
      2. If user_id has 'browser:' prefix, extract base user_id
      3. Lookup user_id in DB if user_id was passed as an access_token / connection_id
    A session is never loaded from another user's directory.
    """
    def _try_read(p: Path) -> dict | None:
        if p.exists():
            try:
                raw = _decrypt(p.read_text())
                if raw:
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return None

    if user_id:
        # 1. Direct path
        res = _try_read(_path_for(user_id, platform))
        if res is not None:
            return res

        # 2. 'browser:' prefix
        if "browser:" in user_id:
            parts = user_id.split(":")
            if len(parts) >= 2 and parts[1]:
                res = _try_read(_path_for(parts[1], platform))
                if res is not None:
                    return res

        # 3. Check DB connections
        try:
            from ... import db
            conn = db.connect()
            rows = conn.execute(
                "SELECT user_id, access_token FROM connections WHERE access_token=? OR id=? OR user_id=?",
                (user_id, user_id, user_id),
            ).fetchall()
            for row in rows:
                if row["user_id"]:
                    res = _try_read(_path_for(row["user_id"], platform))
                    if res is not None:
                        return res
                if row["access_token"]:
                    res = _try_read(_path_for(row["access_token"], platform))
                    if res is not None:
                        return res
        except Exception:
            pass

    return None


def has_session(user_id: str, platform: str) -> bool:
    """Check whether a valid session exists for user or system."""
    return load_session(user_id, platform) is not None


def delete_session(user_id: str, platform: str) -> None:
    """Remove stored session for a user/platform pair."""
    path = _path_for(user_id, platform)
    if path.exists():
        path.unlink()
    
    # Also clean any platform match if user_id was a token
    try:
        if _SESSIONS_DIR.exists():
            for user_dir in _SESSIONS_DIR.iterdir():
                if user_dir.is_dir():
                    c = user_dir / f"{platform}.enc"
                    if c.exists() and user_dir.name == user_id:
                        c.unlink()
    except Exception:
        pass
