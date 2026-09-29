"""Real-data adapter: UCI "Default of Credit Card Clients" (Yeh & Lien, 2009).

30,000 real credit-card customers of a Taiwanese bank (April–September 2005),
with genuine default outcomes and six months of billing / payment / delinquency
history per customer. Source:
https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients

Why this dataset rather than a larger one: it is the only widely-available
public credit dataset that carries a real *monthly* behavioral history, which
is what the early-warning engine needs — it re-scores the same customer at two
points in time instead of thresholding a single snapshot.

Column semantics (from the UCI data dictionary):
  LIMIT_BAL           credit limit (NT$)
  PAY_0, PAY_2..PAY_6 repayment status, most recent (Sep) -> oldest (Apr).
                      -2 = no consumption, -1 = paid in full, 0 = revolving,
                      1..8 = months of payment delay
  BILL_AMT1..6        bill statement amount, most recent (Sep) -> oldest (Apr)
  PAY_AMT1..6         amount paid, most recent (Sep) -> oldest (Apr)
  SEX / MARRIAGE / EDUCATION  demographics — deliberately NOT model features,
                      see PROTECTED_ATTRIBUTES below.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from src.config import ROOT_DIR

DATA_DIR = ROOT_DIR / "data" / "real"
ZIP_PATH = DATA_DIR / "uci_credit.zip"
XLS_PATH = DATA_DIR / "default of credit card clients.xls"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"

# Most-recent-first in the raw file; we reverse to chronological order.
BILL_COLS = ["BILL_AMT6", "BILL_AMT5", "BILL_AMT4", "BILL_AMT3", "BILL_AMT2", "BILL_AMT1"]
PAY_AMT_COLS = ["PAY_AMT6", "PAY_AMT5", "PAY_AMT4", "PAY_AMT3", "PAY_AMT2", "PAY_AMT1"]
STATUS_COLS = ["PAY_6", "PAY_5", "PAY_4", "PAY_3", "PAY_2", "PAY_0"]

TARGET = "default"

NUMERIC_FEATURES = [
    "age",
    "credit_limit",
    "current_balance",
    "credit_utilization",
    "avg_utilization_6m",
    "last_payment",
    "payment_to_bill_ratio",
    "num_late_payments",
    "max_delinquency",
    "months_with_no_usage",
    "utilization_change_30d",
    "utilization_change_60d",
    "utilization_change_90d",
    "balance_change_30d",
    "balance_change_90d",
    "payment_change_30d",
    "late_payments_last_90d",
    "delinquency_trend",
]
CATEGORICAL_FEATURES: list[str] = []
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Kept OUT of the model on purpose and used only by the fair-lending monitor.
# ECOA/Regulation B prohibits using sex or marital status as a basis for a
# credit decision; education is retained here as a proxy-risk segment to
# monitor, not to score on.
PROTECTED_ATTRIBUTES = ["sex", "marriage", "education"]

SEX_LABELS = {1: "Male", 2: "Female"}
MARRIAGE_LABELS = {1: "Married", 2: "Single", 3: "Other", 0: "Unknown"}
EDUCATION_LABELS = {
    1: "Graduate School", 2: "University", 3: "High School",
    4: "Other", 5: "Unknown", 6: "Unknown", 0: "Unknown",
}


def download(force: bool = False) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if XLS_PATH.exists() and not force:
        return XLS_PATH

    resp = requests.get(SOURCE_URL, timeout=120)
    resp.raise_for_status()
    ZIP_PATH.write_bytes(resp.content)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zf.extractall(DATA_DIR)
    return XLS_PATH


def load_raw() -> pd.DataFrame:
    return pd.read_excel(download(), header=1)


def _utilization(bill: pd.Series, limit: pd.Series) -> pd.Series:
    """Balance / credit limit. Negative bills mean the account is in credit
    (overpaid), which is not negative risk — floor at 0. Cap at 2.0 so a few
    over-limit accounts don't dominate the scaler."""
    return (bill / limit.clip(lower=1)).clip(lower=0, upper=2.0)


def build_customers(raw: pd.DataFrame | None = None, as_of_index: int = 5) -> pd.DataFrame:
    """Point-in-time feature frame.

    `as_of_index` selects which month is treated as "now" (5 = September, the
    latest). Passing an earlier index rebuilds every feature as it looked back
    then, which is what the early-warning engine needs to re-score the same
    customer at two points in time. Index 3 is the earliest value that still
    has a full 90-day lookback behind it.
    """
    raw = load_raw() if raw is None else raw
    if not 3 <= as_of_index <= 5:
        raise ValueError("as_of_index must be between 3 and 5 (6 months of history available)")

    limit = raw["LIMIT_BAL"]
    k = as_of_index

    util = [_utilization(raw[c], limit) for c in BILL_COLS]
    bills = [raw[c] for c in BILL_COLS]
    payments = [raw[c] for c in PAY_AMT_COLS]
    status = raw[STATUS_COLS[: k + 1]].to_numpy()
    late_matrix = (status > 0).astype(int)

    df = pd.DataFrame({
        "customer_id": raw["ID"].astype(int),
        "age": raw["AGE"].astype(int),
        "credit_limit": limit.astype(float),
        "current_balance": bills[k].clip(lower=0).astype(float),
        "credit_utilization": util[k].round(4),
        "avg_utilization_6m": pd.concat(util[: k + 1], axis=1).mean(axis=1).round(4),
        "last_payment": payments[k].astype(float),
        # How much of last month's statement was actually paid off.
        "payment_to_bill_ratio": (
            payments[k] / bills[k - 1].clip(lower=1)
        ).clip(lower=0, upper=3).round(4),
        "num_late_payments": late_matrix.sum(axis=1),
        "max_delinquency": status.max(axis=1),
        "months_with_no_usage": (status == -2).sum(axis=1),
        # Behavioral trend block — the early-warning signal, from real history.
        "utilization_change_30d": (util[k] - util[k - 1]).round(4),
        "utilization_change_60d": (util[k] - util[k - 2]).round(4),
        "utilization_change_90d": (util[k] - util[k - 3]).round(4),
        "balance_change_30d": (
            (bills[k] - bills[k - 1]) / bills[k - 1].abs().clip(lower=1)
        ).clip(-5, 5).round(4),
        "balance_change_90d": (
            (bills[k] - bills[k - 3]) / bills[k - 3].abs().clip(lower=1)
        ).clip(-5, 5).round(4),
        "payment_change_30d": (
            (payments[k] - payments[k - 1]) / payments[k - 1].abs().clip(lower=1)
        ).clip(-5, 5).round(4),
        "late_payments_last_90d": late_matrix[:, k - 2:].sum(axis=1),
        # Positive = delinquency worsening over the window.
        "delinquency_trend": (
            raw[STATUS_COLS[k]] - raw[STATUS_COLS[max(0, k - 4)]]
        ).astype(int),
        # Protected attributes: monitored, never scored on.
        "sex": raw["SEX"].map(SEX_LABELS).fillna("Unknown"),
        "marriage": raw["MARRIAGE"].map(MARRIAGE_LABELS).fillna("Unknown"),
        "education": raw["EDUCATION"].map(EDUCATION_LABELS).fillna("Unknown"),
        TARGET: raw["default payment next month"].astype(int),
    })
    return df


def build_history(raw: pd.DataFrame | None = None) -> pd.DataFrame:
    """Long-format monthly history (6 rows per customer, oldest first) so the
    early-warning engine can re-score a customer at two points in time."""
    raw = load_raw() if raw is None else raw
    limit = raw["LIMIT_BAL"]

    frames = []
    for month_index, (bill_col, pay_col, status_col) in enumerate(
        zip(BILL_COLS, PAY_AMT_COLS, STATUS_COLS)
    ):
        frames.append(pd.DataFrame({
            "customer_id": raw["ID"].astype(int),
            "month_index": month_index,
            "bill_amount": raw[bill_col].astype(float),
            "payment_amount": raw[pay_col].astype(float),
            "repayment_status": raw[status_col].astype(int),
            "credit_utilization": _utilization(raw[bill_col], limit).round(4),
        }))

    hist = pd.concat(frames, ignore_index=True).sort_values(["customer_id", "month_index"])
    hist["cumulative_late_payments"] = (
        hist.assign(_late=(hist["repayment_status"] > 0).astype(int))
        .groupby("customer_id")["_late"].cumsum()
    )
    return hist.reset_index(drop=True)


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = load_raw()
    return build_customers(raw), build_history(raw)


if __name__ == "__main__":
    customers, history = load()
    print(f"customers: {customers.shape}, default_rate={customers[TARGET].mean():.4f}")
    print(f"history:   {history.shape}")
    print(customers[ALL_FEATURES].describe().T.to_string())
