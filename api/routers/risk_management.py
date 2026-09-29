import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models import Customer, RiskPrediction
from src.features.engineering import ALL_FEATURES, NUMERIC_FEATURES
from src.models.inference import get_model
from src.models.scoring import risk_level as pd_to_risk_level
from src.monitoring.fairness import group_disparity
from src.risk.expected_loss import portfolio_expected_loss
from src.risk.stress_test import apply_macro_shock, stress_summary

router = APIRouter(tags=["risk-management"])

BEHAVIORAL_TREND_DEFAULTS = {
    "utilization_change_30d": 0.0, "utilization_change_60d": 0.0, "utilization_change_90d": 0.0,
    "balance_change_30d": 0.0, "balance_change_90d": 0.0, "withdrawal_change_30d": 0.0,
    "late_payments_last_90d": 0,
}


@router.get("/portfolio/expected-loss")
def get_expected_loss(db: Session = Depends(get_db)):
    """Portfolio Expected Credit Loss (IFRS 9 / CECL style): EL = PD x LGD x EAD,
    aggregated from each customer's latest stored risk prediction."""
    rows = db.execute(
        select(Customer.customer_id, Customer.total_debt,
               RiskPrediction.probability_of_default, RiskPrediction.risk_level)
        .join(RiskPrediction, RiskPrediction.customer_id == Customer.customer_id)
    ).all()
    df = pd.DataFrame(rows, columns=["customer_id", "total_debt", "probability_of_default", "risk_level"])
    return portfolio_expected_loss(df)


class StressTestRequest(BaseModel):
    unemployment_shock_pp: float = Field(ge=0, le=10, default=2.0, description="Unemployment rate increase, percentage points")
    rate_shock_pp: float = Field(ge=0, le=10, default=2.0, description="Interest rate increase, percentage points")
    sample_size: int = Field(ge=100, le=20000, default=5000)


@router.post("/portfolio/stress-test")
def stress_test(payload: StressTestRequest, db: Session = Depends(get_db)):
    """CCAR/DFAST-style macro scenario: shocks utilization/income/payments and
    re-scores the sampled portfolio with the same PD model used in production,
    comparing baseline vs. stressed risk distribution and expected loss."""
    customers = db.execute(select(Customer).limit(payload.sample_size)).scalars().all()
    rows = [
        {f: getattr(c, f) for f in NUMERIC_FEATURES if hasattr(c, f)}
        | {"occupation": c.occupation, **BEHAVIORAL_TREND_DEFAULTS}
        for c in customers
    ]
    df = pd.DataFrame(rows)
    model = get_model()

    baseline_pd = model.predict_proba(df[ALL_FEATURES])[:, 1]
    shocked_df = apply_macro_shock(df, payload.unemployment_shock_pp, payload.rate_shock_pp)
    stressed_pd = model.predict_proba(shocked_df[ALL_FEATURES])[:, 1]

    baseline_levels = pd.Series(baseline_pd).apply(pd_to_risk_level)
    stressed_levels = pd.Series(stressed_pd).apply(pd_to_risk_level)

    baseline_el = portfolio_expected_loss(pd.DataFrame({
        "probability_of_default": baseline_pd, "total_debt": df["total_debt"], "risk_level": baseline_levels,
    }))
    stressed_el = portfolio_expected_loss(pd.DataFrame({
        "probability_of_default": stressed_pd, "total_debt": df["total_debt"], "risk_level": stressed_levels,
    }))

    return {
        **stress_summary(baseline_pd, stressed_pd),
        "baseline_risk_distribution": baseline_levels.value_counts().to_dict(),
        "stressed_risk_distribution": stressed_levels.value_counts().to_dict(),
        "baseline_expected_loss": baseline_el,
        "stressed_expected_loss": stressed_el,
        "sample_size": len(df),
    }


@router.get("/portfolio/fairness")
def get_fairness(db: Session = Depends(get_db)):
    """Fair-lending disparate-impact screen (EEOC four-fifths rule) across
    occupation groups — see src/monitoring/fairness.py for the compliance caveat."""
    rows = db.execute(
        select(Customer.occupation, RiskPrediction.probability_of_default, RiskPrediction.decision)
        .join(RiskPrediction, RiskPrediction.customer_id == Customer.customer_id)
    ).all()
    df = pd.DataFrame(rows, columns=["occupation", "probability_of_default", "decision"])
    return group_disparity(df, group_col="occupation").to_dict(orient="records")
