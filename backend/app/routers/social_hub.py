"""
Social Hub router for browser-based connections and unified status.
Supports full interactive user authorization flow:
  1. User starts browser session
  2. Browser window opens with platform login page
  3. User logs in manually and handles CAPTCHA/2FA
  4. System detects login & CAPTCHA states in real-time
  5. User explicitly authorizes/approves -> session cookies encrypted and stored
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db, security
from ..agents.graph_schema import PLATFORMS
from ..services import connection_service
from ..social.browser import session_store
from ..social.browser import session_manager
from ..social.unified_registry import BROWSER_ADAPTERS
from ..social.creds import configured as api_configured, PLATFORM_LABELS

router = APIRouter(prefix="/social-hub", tags=["social-hub"])


class TestPostIn(BaseModel):
    text: str = "Test post from Optinum AI Social Hub"


@router.get("/status")
def get_hub_status(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    """Return unified connection status for all platforms (API + Browser)."""
    connections = connection_service.list_for_user(conn, user["id"])
    by_platform = {c["platform"]: c for c in connections}

    status_list = []
    for p in PLATFORMS:
        has_browser = session_store.has_session(user["id"], p)
        has_api = api_configured(p)
        conn_row = by_platform.get(p)
        status_list.append({
            "platform": p,
            "label": PLATFORM_LABELS.get(p, p.capitalize()),
            "api_configured": has_api,
            "browser_connected": has_browser,
            "connection": conn_row,
            "mode": conn_row["mode"] if conn_row else ("browser" if has_browser else ("real" if has_api else "sim")),
            "active": conn_row["status"] == "active" if conn_row else False,
        })
    return status_list


@router.get("/{platform}/browser/status")
def get_browser_status(platform: str, user=Depends(security.get_current_user)):
    """Check if a saved browser session exists for the user on this platform."""
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")
    has_session = session_store.has_session(user["id"], platform)
    return {
        "platform": platform,
        "has_session": has_session,
    }


# ---------------------------------------------------------------------------
# Interactive flow: start -> poll -> approve / cancel
# ---------------------------------------------------------------------------

@router.post("/{platform}/browser/start")
async def start_browser(
    platform: str,
    user=Depends(security.get_current_user),
):
    """
    Launch interactive browser session. Browser window opens on desktop.
    Returns immediately so client can poll and control approval.
    """
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")

    adapter = BROWSER_ADAPTERS.get(platform)
    if adapter is None:
        raise HTTPException(status_code=400, detail=f"No browser adapter for {platform}")

    try:
        session = await session_manager.start_interactive_session(user["id"], platform, adapter)
        return {
            "success": True,
            "status": session.status,
            "platform": platform,
            "url": session.url,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not launch browser: {exc}")


class ChatIn(BaseModel):
    message: str
    context: str = ""


@router.post("/ai-chat")
async def ai_chat(body: ChatIn, user=Depends(security.get_current_user)):
    """AI Marketing and Automation Assistant for Social Hub."""
    from ..llm import chat_with_fallback

    system_prompt = (
        "You are Optinum AI Social & Growth Copilot. You assist users with connecting channels, "
        "setting up automated marketing workflows, bypassing API rate limits with browser workers, "
        "solving CAPTCHAs manually, crafting viral multi-platform content, and optimizing marketing ROI. "
        "Keep your tone sharp, professional, direct, and actionable. Avoid using emojis."
    )
    user_msg = f"User message: {body.message}\nContext: {body.context}" if body.context else body.message
    reply, provider = await chat_with_fallback(system_prompt, user_msg)
    return {"reply": reply, "provider": provider}


@router.get("/{platform}/browser/poll")
async def poll_browser(
    platform: str,
    user=Depends(security.get_current_user),
):
    """Poll the real-time status of the active browser session (CAPTCHA, login state, live screenshot)."""
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")

    session = session_manager.get_interactive_session(user["id"], platform)
    if not session:
        return {
            "active": False,
            "status": "not_started",
            "is_captcha": False,
            "is_logged_in": False,
            "handle": "",
            "url": "",
            "screenshot": None,
        }

    screenshot_b64 = await session.get_screenshot_b64()

    return {
        "active": not session._closed,
        "status": session.status,
        "is_captcha": session.is_captcha,
        "is_logged_in": session.is_logged_in,
        "handle": session.handle,
        "url": session.url,
        "screenshot": screenshot_b64,
    }



@router.post("/{platform}/browser/approve")
async def approve_browser(
    platform: str,
    user=Depends(security.get_current_user),
    conn=Depends(db.get_db),
):
    """
    User authorizes and approves the session.
    Saves encrypted cookies, links connection in database, and closes the browser.
    """
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")

    try:
        res = await session_manager.approve_interactive_session(user["id"], platform)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    handle = res.get("handle") or f"@{user['email'].split('@')[0]}"
    connection = connection_service.link_browser(conn, user["id"], platform, handle)
    return {
        "success": True,
        "handle": handle,
        "connection": connection,
    }


class ImportSessionIn(BaseModel):
    handle: str
    session_json: str = ""


@router.post("/{platform}/browser/import-session")
def import_session(
    platform: str,
    body: ImportSessionIn,
    user=Depends(security.get_current_user),
    conn=Depends(db.get_db),
):
    """Directly link an account or import session state without opening external browser."""
    import json
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")

    handle = body.handle.strip()
    if not handle:
        raise HTTPException(status_code=422, detail="Account handle is required")

    if not handle.startswith("@") and platform != "discord":
        handle = f"@{handle}"

    if body.session_json.strip():
        try:
            state = json.loads(body.session_json)
            session_store.save_session(user["id"], platform, state)
        except Exception:
            pass
    else:
        # Create minimal placeholder session state so publish loader recognizes active session
        state = {"cookies": [], "origins": []}
        session_store.save_session(user["id"], platform, state)

    connection = connection_service.link_browser(conn, user["id"], platform, handle)
    return {
        "success": True,
        "handle": handle,
        "connection": connection,
    }



@router.post("/{platform}/browser/cancel")
async def cancel_browser(
    platform: str,
    user=Depends(security.get_current_user),
):
    """Cancel the active browser session and close the window."""
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")

    cancelled = await session_manager.cancel_interactive_session(user["id"], platform)
    return {"cancelled": cancelled}


# ---------------------------------------------------------------------------
# Fallback / Direct methods
# ---------------------------------------------------------------------------

@router.post("/{platform}/browser/launch")
async def launch_browser_login(
    platform: str,
    user=Depends(security.get_current_user),
    conn=Depends(db.get_db),
):
    """One-shot launch and wait."""
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")

    adapter = BROWSER_ADAPTERS.get(platform)
    if adapter is None:
        raise HTTPException(status_code=400, detail=f"No browser adapter for {platform}")

    result = await adapter.launch_login(user["id"])
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "Browser login failed or timed out."),
        }

    handle = result.get("handle") or f"@{user['email'].split('@')[0]}"
    connection = connection_service.link_browser(conn, user["id"], platform, handle)
    return {
        "success": True,
        "handle": handle,
        "connection": connection,
    }


@router.post("/{platform}/browser/disconnect")
def disconnect_browser(
    platform: str,
    user=Depends(security.get_current_user),
    conn=Depends(db.get_db),
):
    """Remove browser session and disconnect."""
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")
    session_store.delete_session(user["id"], platform)

    existing = conn.execute(
        "SELECT id, mode FROM connections WHERE user_id=? AND platform=?",
        (user["id"], platform),
    ).fetchone()
    if existing and existing["mode"] == "browser":
        connection_service.disconnect(conn, existing["id"], user["id"])

    return {"ok": True}


@router.post("/{platform}/browser/test-post")
async def test_post(
    platform: str,
    body: TestPostIn,
    user=Depends(security.get_current_user),
):
    """Test publishing a post using the stored browser session."""
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail="Unknown platform")

    if not session_store.has_session(user["id"], platform):
        raise HTTPException(
            status_code=400,
            detail=f"No active browser session for {platform}. Connect via browser first.",
        )

    adapter = BROWSER_ADAPTERS.get(platform)
    if adapter is None:
        raise HTTPException(status_code=400, detail="Adapter not found")

    try:
        post_id = await adapter.publish(user["id"], body.text, user_id=user["id"])
        return {"success": True, "post_id": post_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Browser publish failed: {exc}")
