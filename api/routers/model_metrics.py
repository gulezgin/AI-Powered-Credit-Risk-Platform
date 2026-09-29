import json

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import METRICS_PATH
from src.db.database import get_db
from src.db.models import Customer, ModelVersion
from src.features.engineering import NUMERIC_FEATURES
from src.monitoring.drift import compute_feature_drift, population_psi

router = APIRouter(tags=["monitoring"])


@router.get("/model/metrics")
def get_model_metrics(db: Session = Depends(get_db)):
    with open(METRICS_PATH) as f:
        metrics = json.load(f)

    active_version = db.execute(
        select(ModelVersion).where(ModelVersion.is_active.is_(True)).order_by(ModelVersion.trained_at.desc())
    ).scalars().first()

    return {
        "champion_model": metrics["champion_model"],
        "model_version": active_version.version_name if active_version else None,
        "trained_at": active_version.trained_at.isoformat() if active_version else None,
        "comparison": metrics["comparison"],
        "n_train": metrics["n_train"],
        "n_test": metrics["n_test"],
    }


@router.get("/model/monitoring")
def get_model_monitoring(sample_size: int = 3000, db: Session = Depends(get_db)):
    customers = db.execute(select(Customer).limit(sample_size)).scalars().all()
    df = pd.DataFrame([{f: getattr(c, f) for f in NUMERIC_FEATURES if hasattr(c, f)} for c in customers])

    feature_drift = compute_feature_drift(df) if not df.empty else {}
    return {
        "population_psi": population_psi(df) if not df.empty else 0.0,
        "feature_drift": feature_drift,
        "sample_size": len(df),
        "risk_level_distribution": _risk_distribution(db),
    }


def _risk_distribution(db: Session) -> dict:
    from sqlalchemy import func

    from src.db.models import RiskPrediction

    rows = db.execute(
        select(RiskPrediction.risk_level, func.count(RiskPrediction.id))
        .group_by(RiskPrediction.risk_level)
    ).all()
    return {level: count for level, count in rows}


@router.get("/portfolio/summary")
def portfolio_summary(db: Session = Depends(get_db)):
    from sqlalchemy import func

    from src.db.models import RiskAlert, RiskPrediction

    total_customers = db.execute(select(func.count(Customer.customer_id))).scalar_one()
    avg_pd = db.execute(select(func.avg(RiskPrediction.probability_of_default))).scalar_one()
    active_alerts = db.execute(
        select(func.count(RiskAlert.id)).where(RiskAlert.resolved.is_(False))
    ).scalar_one()

    return {
        "total_customers": total_customers,
        "avg_probability_of_default": round(float(avg_pd or 0), 4),
        "active_alerts": active_alerts,
        "risk_level_distribution": _risk_distribution(db),
    }
