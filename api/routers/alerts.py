from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas import AlertOut
from src.db.database import get_db
from src.db.models import RiskAlert

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    resolved: bool | None = None,
    risk_level: str | None = Query(default=None, description="Filter by current_risk_level"),
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(RiskAlert).order_by(RiskAlert.created_at.desc())
    if resolved is not None:
        stmt = stmt.where(RiskAlert.resolved == resolved)
    if risk_level is not None:
        stmt = stmt.where(RiskAlert.current_risk_level == risk_level.upper())
    stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()
