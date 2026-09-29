"""Run the full platform — scoring, decision engine, early warning, expected
loss, fair lending — over the REAL UCI credit-card dataset, and write the
results to artifacts/uci/ for the API and dashboard to serve.

The point of this script is that none of the risk logic is re-implemented here:
it imports the same decision engine, fairness monitor and expected-loss module
the synthetic portfolio uses. Only the data adapter changes.
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from src.config import ARTIFACTS_DIR
from src.datasets import uci_credit
from src.decision.engine import UCI_POLICY, evaluate_application
from src.models.scoring import pd_to_score, risk_level
from src.monitoring.fairness import group_disparity
from src.risk.expected_loss import portfolio_expected_loss

OUT_DIR = ARTIFACTS_DIR / "uci"
EARLY_WARNING_LOOKBACK = 2  # months; 6 months of history total
RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def score(model, df: pd.DataFrame) -> pd.DataFrame:
    proba = model.predict_proba(df[uci_credit.ALL_FEATURES])[:, 1]
    out = df.copy()
    out["probability_of_default"] = proba
    out["risk_score"] = [pd_to_score(p) for p in proba]
    out["risk_level"] = [risk_level(p) for p in proba]
    decisions = [
        evaluate_application(p, requested_amount=lim, income=lim / 12, policy=UCI_POLICY)
        for p, lim in zip(proba, df["credit_limit"])
    ]
    out["decision"] = [d["decision"] for d in decisions]
    out["suggested_interest_rate"] = [d["suggested_interest_rate"] for d in decisions]
    return out


def build_early_warning(model, raw: pd.DataFrame, scored_now: pd.DataFrame) -> list[dict]:
    """Re-score every customer as they looked `EARLY_WARNING_LOOKBACK` months ago
    and flag genuine risk-bucket escalations."""
    past = uci_credit.build_customers(raw, as_of_index=5 - EARLY_WARNING_LOOKBACK)
    past_proba = model.predict_proba(past[uci_credit.ALL_FEATURES])[:, 1]
    past_level = np.array([risk_level(p) for p in past_proba])

    now_level = scored_now["risk_level"].to_numpy()
    now_proba = scored_now["probability_of_default"].to_numpy()

    escalated = np.array([RISK_ORDER[n] > RISK_ORDER[p] for n, p in zip(now_level, past_level)])
    idx = np.where(escalated)[0]

    alerts = []
    for i in idx:
        row_now = scored_now.iloc[i]
        # Codes plus numbers, not sentences: the dashboard is bilingual, so the
        # wording is chosen where the reader's locale is known.
        signals: list[dict] = []
        if row_now["utilization_change_60d"] > 0.10:
            signals.append({
                "code": "utilization_up",
                "params": {"pct": round(row_now["utilization_change_60d"] * 100)},
            })
        if row_now["late_payments_last_90d"] > 0:
            signals.append({
                "code": "late_payments_90d",
                "params": {"count": int(row_now["late_payments_last_90d"])},
            })
        if row_now["delinquency_trend"] > 0:
            signals.append({
                "code": "delinquency_worse",
                "params": {"months": int(row_now["delinquency_trend"])},
            })
        if row_now["payment_change_30d"] < -0.3:
            signals.append({
                "code": "payment_down",
                "params": {"pct": round(abs(row_now["payment_change_30d"]) * 100)},
            })
        if not signals:
            signals.append({"code": "no_dominant_driver", "params": {}})

        alerts.append({
            "customer_id": int(row_now["customer_id"]),
            "previous_risk_level": str(past_level[i]),
            "current_risk_level": str(now_level[i]),
            "previous_pd": round(float(past_proba[i]), 4),
            "current_pd": round(float(now_proba[i]), 4),
            "signals": signals,
            "recommended_action": (
                "immediate_review" if now_level[i] in ("HIGH", "CRITICAL") else "monitor_next_cycle"
            ),
        })
    return alerts


def main():
    model = joblib.load(OUT_DIR / "credit_risk_model.joblib")
    raw = uci_credit.load_raw()
    customers = uci_credit.build_customers(raw)

    scored = score(model, customers)

    # --- Portfolio summary -------------------------------------------------
    risk_distribution = scored["risk_level"].value_counts().to_dict()
    decision_distribution = scored["decision"].value_counts().to_dict()
    summary = {
        "total_customers": int(len(scored)),
        "avg_probability_of_default": round(float(scored["probability_of_default"].mean()), 4),
        "actual_default_rate": round(float(scored[uci_credit.TARGET].mean()), 4),
        "risk_level_distribution": {k: int(v) for k, v in risk_distribution.items()},
        "decision_distribution": {k: int(v) for k, v in decision_distribution.items()},
    }

    # --- Expected loss (EAD = current outstanding balance) ------------------
    el = portfolio_expected_loss(
        scored.rename(columns={"current_balance": "total_debt"}),
        pd_col="probability_of_default",
        ead_col="total_debt",
    )

    # --- Fair lending on REAL protected attributes -------------------------
    fairness = {
        attr: group_disparity(scored, group_col=attr).to_dict(orient="records")
        for attr in uci_credit.PROTECTED_ATTRIBUTES
    }

    # --- Early warning on REAL 6-month behavioral history ------------------
    alerts = build_early_warning(model, raw, scored)

    payload = {
        "summary": summary,
        "expected_loss": el,
        "fairness": fairness,
        "alerts": alerts[:500],
        "alert_count": len(alerts),
        "early_warning_lookback_months": EARLY_WARNING_LOOKBACK,
    }
    with open(OUT_DIR / "portfolio_analysis.json", "w") as f:
        json.dump(payload, f, indent=2)

    scored_cols = [
        "customer_id", "probability_of_default", "risk_score", "risk_level", "decision",
        "credit_limit", "current_balance", "credit_utilization", "age",
        *uci_credit.PROTECTED_ATTRIBUTES, uci_credit.TARGET,
    ]
    scored[scored_cols].to_csv(OUT_DIR / "scored_customers.csv", index=False)

    # --- Report ------------------------------------------------------------
    print(f"Customers scored: {summary['total_customers']:,}")
    print(f"Actual default rate: {summary['actual_default_rate']:.2%} | "
          f"Model avg PD: {summary['avg_probability_of_default']:.2%}")
    print(f"Risk levels: {summary['risk_level_distribution']}")
    print(f"Decisions:   {summary['decision_distribution']}")
    print(f"\nExpected loss: {el['total_expected_loss']:,.0f} NT$ "
          f"({el['expected_loss_ratio']:.2%} of {el['total_exposure']:,.0f} NT$ exposure)")
    print(f"\nEarly warning alerts (real behavioral escalation): {len(alerts):,}")

    print("\n--- FAIR LENDING (real protected attributes) ---")
    for attr, rows in fairness.items():
        print(f"\n{attr.upper()}")
        for r in rows:
            flag = "  <-- FLAGGED" if r["flagged"] else ""
            print(f"  {r[attr]:<16} n={r['n']:>6,}  avg_pd={r['avg_pd']:.2%}  "
                  f"approval={r['approval_rate']:.2%}  AIR={r['adverse_impact_ratio']:.3f}{flag}")


if __name__ == "__main__":
    main()
