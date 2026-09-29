"""Serves the results of running the platform over the REAL UCI Taiwanese
credit-card dataset, so the dashboard can show the synthetic demo portfolio and
the real benchmark side by side.

These endpoints read precomputed artifacts (written by
`scripts/analyze_real_dataset.py`) rather than scoring 30k customers per
request — the analysis is a batch job, the same way a bank would run portfolio
analytics on a schedule rather than on page load.
"""
from __future__ import annotations

import json
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from src.config import ARTIFACTS_DIR, METRICS_PATH

router = APIRouter(prefix="/real-dataset", tags=["real-dataset"])

UCI_DIR = ARTIFACTS_DIR / "uci"

PROVENANCE = {
    "name": "Default of Credit Card Clients",
    "source": "UCI Machine Learning Repository (dataset 350)",
    "url": "https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients",
    "citation": "Yeh, I.-C. & Lien, C.-H. (2009), Expert Systems with Applications 36(2), 2473-2480",
    "origin": "A Taiwanese bank's credit card portfolio, April-September 2005",
    "n_customers": 30000,
    "history_months": 6,
    "target": "Default on the next month's payment",
    "excluded_from_model": ["sex", "marriage", "education"],
    "excluded_reason": (
        "ECOA/Regulation B prohibits basing a credit decision on sex or marital "
        "status; education is withheld as a proxy risk. All three are used only "
        "by the fair-lending monitor."
    ),
}


def _read(path_name: str) -> dict:
    path = UCI_DIR / path_name
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                f"{path_name} not found. Run `python -m src.models.train --dataset uci` "
                "then `python -m scripts.analyze_real_dataset`."
            ),
        )
    with open(path) as f:
        return json.load(f)


@lru_cache(maxsize=4)
def _cached(path_name: str) -> dict:
    return _read(path_name)


@router.get("/provenance")
def provenance():
    return PROVENANCE


@router.get("/metrics")
def metrics():
    """Real-data model metrics alongside the synthetic ones, so the gap between
    a flattering synthetic benchmark and a real portfolio is explicit."""
    real = _cached("model_metrics.json")
    payload = {"real": real}

    if METRICS_PATH.exists():
        with open(METRICS_PATH) as f:
            payload["synthetic"] = json.load(f)
    return payload


@router.get("/summary")
def summary():
    analysis = _cached("portfolio_analysis.json")
    return {
        **analysis["summary"],
        "expected_loss": analysis["expected_loss"],
        "alert_count": analysis["alert_count"],
        "early_warning_lookback_months": analysis["early_warning_lookback_months"],
    }


@router.get("/fairness")
def fairness():
    return _cached("portfolio_analysis.json")["fairness"]


@router.get("/alerts")
def alerts(limit: int = Query(default=50, le=500)):
    return _cached("portfolio_analysis.json")["alerts"][:limit]
