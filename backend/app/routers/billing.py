from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db, security

router = APIRouter(prefix="/billing", tags=["billing"])

TIERS = {
    "free": {"label": "Starter", "price": 0, "agents": 25, "tokens": "5M", "nodes": 3},
    "growth": {"label": "Growth Pro", "price": 1250, "agents": 50, "tokens": "10M", "nodes": 8},
    "unlimited": {"label": "Optinum Unlimited", "price": 4850, "agents": 500, "tokens": "100M", "nodes": 20},
}


class UpgradeIn(BaseModel):
    tier: str


@router.get("")
def billing(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    tier = TIERS.get(user["plan"], TIERS["free"])
    executions = conn.execute("SELECT COUNT(*) AS c FROM executions WHERE user_id=?", (user["id"],)).fetchone()["c"]
    connections = conn.execute("SELECT COUNT(*) AS c FROM connections WHERE user_id=?", (user["id"],)).fetchone()["c"]
    return {
        "plan": user["plan"],
        "tier": tier,
        "quotas": {
            "agents": {"used": min(tier["agents"], 8 + executions * 4), "max": tier["agents"]},
            "tokens": {"used_label": f"{1.2 + executions * 0.4:.1f}M", "max": tier["tokens"]},
            "nodes": {"used": connections, "max": tier["nodes"]},
        },
        "invoices": [
            {"id": "INV-2049", "date": "2026-08-01", "amount": f"${tier['price']:,}", "status": "PAID"},
            {"id": "INV-2012", "date": "2026-07-01", "amount": f"${tier['price']:,}", "status": "PAID"},
        ],
    }


@router.post("/upgrade")
def upgrade(body: UpgradeIn, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    if body.tier not in TIERS:
        raise HTTPException(status_code=422, detail="Unknown tier")
    conn.execute("UPDATE users SET plan=? WHERE id=?", (body.tier, user["id"]))
    conn.commit()
    return {"plan": body.tier, "tier": TIERS[body.tier]}
