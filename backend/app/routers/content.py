import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from .. import config, db, security
from ..agents import orchestrator
from ..agents.graph_schema import PLATFORMS
from ..security import new_id, now_iso
from ..social.registry import get_adapter

router = APIRouter(prefix="/content", tags=["content"])

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif", "mp4", "webm"}


class SuggestIn(BaseModel):
    topic: str = ""
    tone: str = "bold"


@router.post("/suggest")
async def suggest(body: SuggestIn, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    product = conn.execute(
        "SELECT name, description FROM products WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
        (user["id"],),
    ).fetchone()
    topic = body.topic or (product["name"] if product else "your product")
    node = {"id": "manual", "type": "content", "params": {"tone": body.tone, "format": "text_post", "cta": "signup"}}
    ctx = {"content": {"tone": body.tone, "format": "text_post", "cta": "signup"},
           "audience": {"segment": "marketers"}, "channel": {"platform": "linkedin"}}
    posts, provider = await orchestrator.generate_posts(node, ctx, {"name": topic, "description": ""}, 1)
    return {"text": posts[0] if posts else "", "provider": provider}


@router.post("/publish")
async def publish(
    text: str = Form(""),
    platforms: str = Form("[]"),
    file: UploadFile | None = File(None),
    user=Depends(security.get_current_user),
    conn=Depends(db.get_db),
):
    if not text.strip() and file is None:
        raise HTTPException(status_code=422, detail="Add a caption or upload an asset first")
    try:
        selected = json.loads(platforms or "[]")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Platforms must be a JSON array") from exc
    if not isinstance(selected, list):
        raise HTTPException(status_code=422, detail="One or more selected channels are invalid")
    if not selected:
        raise HTTPException(status_code=422, detail="Pick at least one channel")
    if any(not isinstance(platform, str) or platform not in PLATFORMS for platform in selected):
        raise HTTPException(status_code=422, detail="One or more selected channels are invalid")

    asset_path = None
    file_bytes = None
    filename = None
    if file is not None:
        suffix = (file.filename or "asset.bin").rsplit(".", 1)[-1].lower()
        if suffix not in ALLOWED_EXT:
            raise HTTPException(status_code=422, detail=f"Unsupported asset type .{suffix}")
        file_bytes = await file.read()
        filename = file.filename
        asset_path = f"/uploads/content_{new_id('ast')}.{suffix}"
        (config.UPLOAD_DIR / asset_path.removeprefix("/uploads/")).write_bytes(file_bytes)

    results = []
    from ..social.browser import session_store
    for platform in selected:
        adapter = get_adapter(platform)
        row = conn.execute(
            "SELECT id, mode, access_token FROM connections "
            "WHERE user_id=? AND platform=? AND status='active' AND enabled=1",
            (user["id"], platform),
        ).fetchone()
        has_browser = session_store.has_session(user["id"], platform)
        live = bool((row and row["mode"] in ("real", "browser")) or has_browser) and adapter and adapter.configured()
        status, external_id, error = "published_sim", None, None
        if live:
            tok = (row["access_token"] if row and row["access_token"] else user["id"])
            try:
                if file_bytes is not None:
                    external_id = await adapter.publish_media(tok, text, file_bytes, filename)
                else:
                    external_id = await adapter.publish(tok, text)
                status = "published"
            except Exception as exc:
                error = str(exc)
                status = "auth_required" if "Authentication required" in error else "failed"
        cid = new_id("cpt")
        conn.execute(
            "INSERT INTO content_posts (id, user_id, platform, content_text, asset_path, status, external_id, error, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, user["id"], platform, text, asset_path, status, external_id, error, now_iso()),
        )
        results.append({"platform": platform, "status": status, "mode": "live" if live else "sim", "error": error})
    conn.commit()
    return {"results": results, "asset_path": asset_path}


@router.get("/history")
def history(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    rows = conn.execute(
        "SELECT * FROM content_posts WHERE user_id=? ORDER BY created_at DESC LIMIT 50", (user["id"],)
    ).fetchall()
    return [dict(r) for r in rows]
