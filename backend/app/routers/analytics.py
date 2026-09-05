from fastapi import APIRouter, Depends

from .. import db, security
from ..services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    return analytics_service.overview(conn, user["id"])


@router.get("/engagement")
def engagement(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    return analytics_service.engagement(conn, user["id"])


@router.get("/performance")
def performance():
    return analytics_service.performance()


@router.get("/recommend")
async def recommend(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    return await analytics_service.recommend(conn, user["id"])


@router.get("/insights")
async def insights(user=Depends(security.get_current_user), conn=Depends(db.get_db)):
    return await analytics_service.insights(conn, user["id"])
