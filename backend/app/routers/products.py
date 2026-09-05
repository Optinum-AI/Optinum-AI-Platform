import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from .. import config, db, security
from ..services import product_service

router = APIRouter(prefix="/products", tags=["products"])

PRESETS = {
    "Nexus": "Autonomous multi-agent customer acquisition, tier qualification, and cross-channel CRM reconciliation pipeline with automated revenue recovery.",
    "OmniFlow": "Unified workflow orchestration that routes every inbound signal to the right autonomous agent in real time.",
    "FinPulse": "Real-time revenue intelligence for finance teams: anomaly alerts, forecast drift, and automated reconciliation.",
}


class ProductIn(BaseModel):
    name: str
    description: str = ""
    preset: str | None = None


@router.post("")
async def create(body: ProductIn, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Product name required")
    description = body.description.strip() or PRESETS.get(body.preset or "", "")
    product, strategy, provider = await product_service.create(conn, user["id"], name, description, body.preset)
    return {"product": product, "strategy": strategy, "provider": provider}


@router.get("")
def list_products(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    rows = conn.execute("SELECT * FROM products WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@router.get("/{product_id}")
def get_product(product_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    row = conn.execute("SELECT * FROM products WHERE id=? AND user_id=?", (product_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)


@router.post("/{product_id}/logo")
def upload_logo(product_id: str, file: UploadFile, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    row = conn.execute("SELECT id FROM products WHERE id=? AND user_id=?", (product_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    suffix = (file.filename or "logo.png").rsplit(".", 1)[-1].lower()
    if suffix not in ("png", "jpg", "jpeg", "webp", "svg"):
        raise HTTPException(status_code=422, detail="Unsupported image type")
    path = config.UPLOAD_DIR / f"{product_id}.{suffix}"
    with path.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    conn.execute("UPDATE products SET logo_path=? WHERE id=?", (f"/uploads/{path.name}", product_id))
    conn.commit()
    return {"logo_path": f"/uploads/{path.name}"}
