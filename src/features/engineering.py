"""Feature engineering: joins static customer attributes with derived
behavioral-trend features computed from the monthly credit_history table."""
from __future__ import annotations

import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "age",
    "income",
    "employment_years",
    "credit_history_years",
    "num_existing_loans",
    "num_credit_inquiries_6m",
    "total_debt",
    "monthly_payment",
    "credit_utilization",
    "num_late_payments",
    "account_balance",
    "transaction_intensity",
    "debt_to_income",
    "payment_to_income",
    "utilization_change_30d",
    "utilization_change_60d",
    "utilization_change_90d",
    "balance_change_30d",
    "balance_change_90d",
    "withdrawal_change_30d",
    "late_payments_last_90d",
]
CATEGORICAL_FEATURES = ["occupation"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "default"


def build_behavioral_features(history: pd.DataFrame, as_of_month_index: int | None = None) -> pd.DataFrame:
    """Collapse each customer's monthly history into point-in-time trend features.

    `as_of_month_index` lets the caller re-derive features as they looked N
    months ago (used by the early-warning engine to re-score a customer at two
    points in time and detect a real risk-bucket transition). Defaults to the
    latest available month.
    """
    history = history.sort_values(["customer_id", "month_index"])
    last_month = as_of_month_index if as_of_month_index is not None else history["month_index"].max()

    def _snapshot(g: pd.DataFrame, months_back: int) -> pd.Series:
        target_m = last_month - months_back
        candidates = g[g["month_index"] <= target_m]
        if candidates.empty:
            return g.iloc[0]
        return candidates.iloc[-1]

    out = []
    for cust_id, g in history.groupby("customer_id", sort=False):
        now_rows = g[g["month_index"] == last_month]
        if now_rows.empty:
            continue
        now = now_rows.iloc[0]
        m1 = _snapshot(g, 1)
        m2 = _snapshot(g, 2)
        m3 = _snapshot(g, 3)

        util_now = now["credit_utilization"]
        util_30 = util_now - m1["credit_utilization"]
        util_60 = util_now - m2["credit_utilization"]
        util_90 = util_now - m3["credit_utilization"]

        bal_now = now["account_balance"]
        bal_30 = (bal_now - m1["account_balance"]) / (m1["account_balance"] + 1e-6)
        bal_90 = (bal_now - m3["account_balance"]) / (m3["account_balance"] + 1e-6)

        wd_now = now["cash_withdrawal_count"]
        wd_30 = (wd_now - m1["cash_withdrawal_count"]) / (m1["cash_withdrawal_count"] + 1e-6)

        late_recent = now["cumulative_late_payments"] - m3["cumulative_late_payments"]

        out.append({
            "customer_id": cust_id,
            "utilization_change_30d": round(float(util_30), 4),
            "utilization_change_60d": round(float(util_60), 4),
            "utilization_change_90d": round(float(util_90), 4),
            "balance_change_30d": round(float(bal_30), 4),
            "balance_change_90d": round(float(bal_90), 4),
            "withdrawal_change_30d": round(float(wd_30), 4),
            "late_payments_last_90d": int(max(0, late_recent)),
            "current_utilization_snapshot": round(float(util_now), 4),
        })
    return pd.DataFrame(out)


def build_training_frame(customers: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    behavior = build_behavioral_features(history)
    df = customers.merge(behavior, on="customer_id", how="left")
    return df


def select_model_matrix(df: pd.DataFrame):
    X = df[ALL_FEATURES].copy()
    y = df[TARGET].copy() if TARGET in df.columns else None
    return X, y
