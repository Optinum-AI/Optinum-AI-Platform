from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from urllib.parse import quote
import secrets

from .. import config, db, security
from ..agents.graph_schema import PLATFORMS
from ..services import connection_service
from ..social.registry import get_adapter

router = APIRouter(prefix="/connections", tags=["connections"])


class LinkIn(BaseModel):
    handle: str = ""


class ToggleIn(BaseModel):
    enabled: bool = True


@router.get("")
def list_connections(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    return connection_service.list_for_user(conn, user["id"])


@router.get("/{platform}/oauth/start")
def oauth_start(platform: str, user=Depends(security.get_current_user)):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")
    adapter = get_adapter(platform)
    if adapter is None or not adapter.configured():
        raise HTTPException(
            status_code=409,
            detail=(
                f"Live OAuth for {platform} is not configured. Add your developer-app credentials to "
                f"backend/.env (see README 'Connecting real accounts'), or continue in labeled SIM mode."
            ),
        )
    verifier = secrets.token_urlsafe(64) if platform == "tiktok" else None
    state = security.create_oauth_state(user_id=user["id"], platform=platform, flow=verifier)
    redirect_uri = f"{config.OAUTH_REDIRECT_BASE}/api/connections/{platform}/oauth/callback"
    return {"url": adapter.auth_url(state, redirect_uri)}


@router.get("/{platform}/oauth/callback")
async def oauth_callback(
    platform: str,
    code: str = "",
    state: str = "",
    error: str = "",
    error_message: str = "",
    conn=Depends(db.get_db),
):
    if error:
        detail = error_message or error
        return RedirectResponse(
            f"{config.FRONTEND_BASE}/social-hub?error=oauth_provider_error&detail={quote(detail)}"
        )
    payload = security.decode_oauth_state(state)
    if payload.get("plat") != platform:
        raise HTTPException(status_code=400, detail="State/platform mismatch")
    adapter = get_adapter(platform)
    if adapter is None or not adapter.configured():
        raise HTTPException(status_code=409, detail=f"{platform} adapter not configured")
    redirect_uri = f"{config.OAUTH_REDIRECT_BASE}/api/connections/{platform}/oauth/callback"
    try:
        if platform == "tiktok":
            tokens = await adapter.exchange_code(code, redirect_uri, payload.get("flow", ""))
        else:
            tokens = await adapter.exchange_code(code, redirect_uri)
        handle = await adapter.me(tokens["access_token"])
    except Exception as exc:
        return RedirectResponse(f"{config.FRONTEND_BASE}/social-hub?error=oauth_failed")
    connection_service.link_real(conn, payload["sub"], platform, tokens, handle)
    return RedirectResponse(f"{config.FRONTEND_BASE}/social-hub?linked={platform}")


@router.post("/{platform}/link")
def link(platform: str, body: LinkIn, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")
    handle = body.handle or f"@{user['email'].split('@')[0]}"
    return connection_service.link(conn, user["id"], platform, handle)


@router.post("/{connection_id}/toggle")
def toggle(connection_id: str, body: ToggleIn, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    row = connection_service.toggle_enabled(conn, connection_id, user["id"], body.enabled)
    if not row:
        raise HTTPException(status_code=404, detail="Connection not found")
    return row


@router.post("/{connection_id}/resync")
async def resync(connection_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    row = connection_service.resync(conn, connection_id, user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Connection not found")
    synced = await connection_service.sync_metrics(conn, row)
    return {**row, "metrics_synced": synced}


@router.post("/{connection_id}/disconnect")
def disconnect(connection_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    if not connection_service.disconnect(conn, connection_id, user["id"]):
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"ok": True}
