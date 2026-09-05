import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from urllib.parse import urlencode

from .. import config, db, security
from ..social import creds

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupIn(BaseModel):
    email: str
    password: str
    full_name: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


def public_user(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "plan": user["plan"]}


@router.post("/signup")
def signup(body: SignupIn, conn=Depends(db.get_db)):
    email = body.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Invalid email")
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    if conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
        raise HTTPException(status_code=409, detail="Email already registered")
    uid = security.new_id("usr")
    conn.execute(
        "INSERT INTO users (id, email, password_hash, full_name, created_at) VALUES (?,?,?,?,?)",
        (uid, email, security.hash_password(body.password), body.full_name.strip(), security.now_iso()),
    )
    conn.commit()
    return {"token": security.create_token(uid), "user": {"id": uid, "email": email, "full_name": body.full_name.strip(), "plan": "free"}}


@router.post("/login")
def login(body: LoginIn, conn=Depends(db.get_db)):
    row = conn.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
    if not row or not security.verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": security.create_token(row["id"]), "user": public_user(dict(row))}


@router.get("/me")
def me(user=Depends(security.get_current_user)):
    return public_user(user)


@router.get("/providers")
def providers():
    return {"google": creds.configured("google")}


@router.get("/google/start")
def google_start():
    if not creds.configured("google"):
        raise HTTPException(
            status_code=409,
            detail=(
                "Google Sign-In is not configured. Paste your Google OAuth client ID and secret in "
                "Integrations (sidebar) or backend/.env — it takes 2 minutes in Google Cloud Console."
            ),
        )
    cid, _ = creds.get("google")
    state = security.create_oauth_state(flow="google")
    redirect_uri = f"{config.OAUTH_REDIRECT_BASE}/api/auth/google/callback"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        {
            "client_id": cid,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
    )
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str = "", state: str = "", conn=Depends(db.get_db)):
    payload = security.decode_oauth_state(state)
    if payload.get("flow") != "google":
        raise HTTPException(status_code=400, detail="OAuth flow mismatch")
    cid, csec = creds.get("google")
    redirect_uri = f"{config.OAUTH_REDIRECT_BASE}/api/auth/google/callback"
    async with httpx.AsyncClient(timeout=30) as client:
        token_r = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": cid,
                "client_secret": csec,
            },
        )
        if token_r.status_code != 200:
            return RedirectResponse(f"{config.FRONTEND_BASE}/login?error=google_oauth_failed")
        access_token = token_r.json()["access_token"]
        info_r = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info_r.raise_for_status()
        info = info_r.json()
    email = (info.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if row:
        uid = row["id"]
    else:
        uid = security.new_id("usr")
        conn.execute(
            "INSERT INTO users (id, email, password_hash, full_name, created_at) VALUES (?,?,?,?,?)",
            (uid, email, "google-oauth-no-password", info.get("name", ""), security.now_iso()),
        )
        conn.commit()
    token = security.create_token(uid)
    return RedirectResponse(f"{config.FRONTEND_BASE}/auth/google#token={token}")
