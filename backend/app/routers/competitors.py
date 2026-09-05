import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db, security
from ..agents import orchestrator
from ..security import now_iso

router = APIRouter(prefix="/competitors", tags=["competitors"])


class CompetitorIn(BaseModel):
    name: str
    notes: str = ""
    url: str = ""


@router.post("")
def create(body: CompetitorIn, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    if not body.name.strip():
        raise HTTPException(status_code=422, detail="Name required")
    cid = security.new_id("cmp")
    now = now_iso()
    conn.execute(
        "INSERT INTO competitors (id, user_id, name, notes, url, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (cid, user["id"], body.name.strip(), body.notes, body.url, now, now),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM competitors WHERE id=?", (cid,)).fetchone())


@router.get("")
def list_competitors(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    rows = conn.execute("SELECT * FROM competitors WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@router.delete("/{competitor_id}")
def delete(competitor_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    cur = conn.execute("DELETE FROM competitors WHERE id=? AND user_id=?", (competitor_id, user["id"]))
    conn.commit()
    if not cur.rowcount:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"ok": True}


@router.post("/{competitor_id}/analyze")
async def analyze(competitor_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    row = conn.execute("SELECT * FROM competitors WHERE id=? AND user_id=?", (competitor_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Competitor not found")
    product = conn.execute(
        "SELECT * FROM products WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user["id"],)
    ).fetchone()
    product_dict = {"name": product["name"], "description": product["description"]} if product else {"name": "your product"}
    analysis, provider = await orchestrator.compare_competitor(product_dict, dict(row))
    conn.execute(
        "UPDATE competitors SET analysis_json=?, updated_at=? WHERE id=?",
        (json.dumps({**analysis, "provider": provider}), now_iso(), competitor_id),
    )
    conn.commit()
    return {**analysis, "provider": provider}
