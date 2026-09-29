"""Early-warning engine: re-scores a customer's model PD at two points in time
(now vs. `lookback_months` ago) using the same champion model, and flags a
real transition between risk buckets rather than a one-off threshold breach."""
from __future__ import annotations

import joblib
import pandas as pd

from src.config import MODEL_PATH
from src.features.engineering import ALL_FEATURES, build_behavioral_features
from src.models.scoring import risk_level

RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _score(model, customers: pd.DataFrame, behavior: pd.DataFrame) -> pd.DataFrame:
    df = customers.merge(behavior, on="customer_id", how="inner")
    proba = model.predict_proba(df[ALL_FEATURES])[:, 1]
    df = df.assign(pd_value=proba)
    df["risk_level"] = df["pd_value"].apply(risk_level)
    return df[["customer_id", "pd_value", "risk_level"]]


def build_signals(
    customer_row: pd.Series, current_hist_row: pd.Series, past_hist_row: pd.Series
) -> list[dict]:
    """Signals are emitted as a code plus its numbers, not as a finished
    sentence. The dashboard ships in more than one language, so the wording has
    to be chosen where the reader's locale is known."""
    signals: list[dict] = []

    util_change = current_hist_row["credit_utilization"] - past_hist_row["credit_utilization"]
    if util_change > 0.15:
        signals.append({"code": "utilization_up", "params": {"pct": round(util_change * 100)}})

    bal_change = current_hist_row["account_balance"] - past_hist_row["account_balance"]
    if bal_change < 0 and past_hist_row["account_balance"] > 0:
        pct = abs(bal_change / past_hist_row["account_balance"] * 100)
        signals.append({"code": "balance_down", "params": {"pct": round(pct)}})

    late_change = current_hist_row["cumulative_late_payments"] - past_hist_row["cumulative_late_payments"]
    if late_change > 0:
        signals.append({"code": "new_late_payments", "params": {"count": int(late_change)}})

    wd_past = max(1, past_hist_row["cash_withdrawal_count"])
    wd_change_pct = (current_hist_row["cash_withdrawal_count"] - wd_past) / wd_past * 100
    if wd_change_pct > 25:
        signals.append({"code": "withdrawals_up", "params": {"pct": round(wd_change_pct)}})

    return signals


def detect_customer_alert(
    customers: pd.DataFrame, history: pd.DataFrame, customer_id: int,
    lookback_months: int = 3, model=None,
) -> dict | None:
    """Single-customer convenience wrapper. For scanning many customers, use
    `scan_for_alerts` instead — it computes population-wide behavioral
    features once instead of re-deriving them per customer."""
    model = model or joblib.load(MODEL_PATH)
    cust_row = customers[customers["customer_id"] == customer_id]
    hist_c = history[history["customer_id"] == customer_id]
    if cust_row.empty or hist_c.empty:
        return None
    results = scan_for_alerts(cust_row, hist_c, [customer_id], lookback_months, model)
    return results[0] if results else None


def scan_for_alerts(
    customers: pd.DataFrame, history: pd.DataFrame, candidate_ids: list[int],
    lookback_months: int = 3, model=None,
) -> list[dict]:
    """Batch version: computes behavioral features and model PD for the whole
    population at two points in time ONCE, then evaluates every candidate."""
    model = model or joblib.load(MODEL_PATH)
    last_month = history["month_index"].max()
    past_month = max(0, last_month - lookback_months)

    behavior_now = build_behavioral_features(history, as_of_month_index=last_month)
    behavior_past = build_behavioral_features(history, as_of_month_index=past_month)

    now_scored = _score(model, customers, behavior_now).set_index("customer_id")
    past_scored = _score(model, customers, behavior_past).set_index("customer_id")

    history_sorted = history.sort_values("month_index")
    now_hist = history_sorted[history_sorted["month_index"] == last_month].set_index("customer_id")
    past_hist = (
        history_sorted[history_sorted["month_index"] <= past_month]
        .groupby("customer_id").last()
    )
    customers_idx = customers.set_index("customer_id")

    alerts = []
    for cid in candidate_ids:
        if cid not in now_scored.index or cid not in past_scored.index:
            continue
        if cid not in now_hist.index or cid not in past_hist.index:
            continue

        now_risk = now_scored.loc[cid]
        past_risk = past_scored.loc[cid]
        signals = build_signals(customers_idx.loc[cid], now_hist.loc[cid], past_hist.loc[cid])
        escalated = RISK_ORDER[now_risk["risk_level"]] > RISK_ORDER[past_risk["risk_level"]]

        if not (escalated or len(signals) >= 2):
            continue

        alerts.append({
            "customer_id": int(cid),
            "previous_risk_level": past_risk["risk_level"],
            "current_risk_level": now_risk["risk_level"],
            "previous_pd": round(float(past_risk["pd_value"]), 4),
            "current_pd": round(float(now_risk["pd_value"]), 4),
            "signals": signals,
            "recommended_action": (
                "immediate_review" if now_risk["risk_level"] in ("HIGH", "CRITICAL")
                else "monitor_next_cycle"
            ),
        })
    return alerts


def monthly_trend(history: pd.DataFrame, customer_id: int) -> list[dict]:
    hist_c = history[history["customer_id"] == customer_id].sort_values("month_index")
    return [
        {
            "month_index": int(r["month_index"]),
            "credit_utilization": round(float(r["credit_utilization"]), 4),
            "account_balance": round(float(r["account_balance"]), 2),
        }
        for _, r in hist_c.iterrows()
    ]
