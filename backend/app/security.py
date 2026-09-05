import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from . import config, db

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_ctx.verify(password, hashed)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=config.TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def create_oauth_state(user_id: str | None = None, platform: str | None = None, flow: str | None = None) -> str:
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        "nonce": uuid.uuid4().hex,
    }
    if user_id:
        payload["sub"] = user_id
    if platform:
        payload["plat"] = platform
    if flow:
        payload["flow"] = flow
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_oauth_state(state: str) -> dict:
    try:
        return jwt.decode(state, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state") from exc


def get_current_user(
    conn=Depends(db.get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    row = conn.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return dict(row)
