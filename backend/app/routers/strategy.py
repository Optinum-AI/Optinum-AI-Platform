import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db, security
from ..agents import graph_schema as gs
from ..security import now_iso
from ..services import execution_service

router = APIRouter(tags=["strategy"])


class GraphIn(BaseModel):
    graph: dict


def _get_strategy(conn, strategy_id: str, user_id: str) -> dict:
    row = conn.execute("SELECT * FROM strategies WHERE id=? AND user_id=?", (strategy_id, user_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return dict(row)


@router.get("/strategies/{strategy_id}")
def get_strategy(strategy_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    strategy = _get_strategy(conn, strategy_id, user["id"])
    product = conn.execute("SELECT * FROM products WHERE id=?", (strategy["product_id"],)).fetchone()
    return {**strategy, "graph": json.loads(strategy["graph_json"]), "product": dict(product)}


@router.put("/strategies/{strategy_id}")
def update_strategy(strategy_id: str, body: GraphIn, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    strategy = _get_strategy(conn, strategy_id, user["id"])
    errors = gs.validate_graph(body.graph)
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    conn.execute(
        "UPDATE strategies SET graph_json=?, version=version+1, updated_at=? WHERE id=?",
        (json.dumps(body.graph), now_iso(), strategy_id),
    )
    conn.commit()
    return {"ok": True, "version": strategy["version"] + 1}


@router.post("/strategies/{strategy_id}/run")
async def run_strategy(strategy_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    strategy = _get_strategy(conn, strategy_id, user["id"])
    exec_id = security.new_id("exe")
    conn.execute(
        "INSERT INTO executions (id, strategy_id, user_id, status, started_at, logs_json) VALUES (?,?,?,'running',?,'[]')",
        (exec_id, strategy_id, user["id"], now_iso()),
    )
    conn.commit()
    asyncio.create_task(execution_service.run(exec_id, strategy, user["id"]))
    return {"execution_id": exec_id}


@router.get("/strategies/{strategy_id}/executions")
def list_executions(strategy_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    _get_strategy(conn, strategy_id, user["id"])
    rows = conn.execute(
        "SELECT * FROM executions WHERE strategy_id=? ORDER BY started_at DESC", (strategy_id,)
    ).fetchall()
    return [{**dict(r), "logs": json.loads(r["logs_json"])} for r in rows]


@router.get("/strategies/{strategy_id}/posts")
def list_posts(strategy_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    _get_strategy(conn, strategy_id, user["id"])
    rows = conn.execute(
        """
        SELECT p.*, m.impressions, m.likes, m.comments, m.shares, m.clicks
        FROM posts p
        LEFT JOIN metrics m ON m.post_id = p.id
        WHERE p.execution_id IN (SELECT id FROM executions WHERE strategy_id=?)
        ORDER BY p.scheduled_at ASC
        """,
        (strategy_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/executions/{execution_id}")
def get_execution(execution_id: str, user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    row = conn.execute("SELECT * FROM executions WHERE id=? AND user_id=?", (execution_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {**dict(row), "logs": json.loads(row["logs_json"])}
