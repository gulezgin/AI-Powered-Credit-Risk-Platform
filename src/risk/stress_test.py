"""Macro stress testing, in the spirit of the Fed's CCAR/DFAST severely-adverse
scenarios: shock a small number of macro-linked features and re-run the same
PD model to see how the portfolio's risk distribution and expected loss move.

The transmission mechanism is a simplified, transparent, documented
assumption set (not a fitted macro model) — appropriate for a portfolio demo,
and worth being explicit about to anyone using the numbers:

- unemployment_shock_pp (percentage points): pushes revolving utilization up
  and income down, reflecting households drawing on credit and losing hours/
  jobs.
- rate_shock_pp (percentage points): repriced monthly payments on
  variable-rate debt increase, raising payment-to-income and debt-to-income.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

UTILIZATION_SENSITIVITY = 0.02   # +2pp utilization per +1pp unemployment
INCOME_SENSITIVITY = 0.015        # -1.5% income per +1pp unemployment
PAYMENT_RATE_SENSITIVITY = 0.08   # +8% monthly payment per +1pp rate shock


def apply_macro_shock(df: pd.DataFrame, unemployment_shock_pp: float, rate_shock_pp: float) -> pd.DataFrame:
    shocked = df.copy()

    shocked["credit_utilization"] = np.clip(
        shocked["credit_utilization"] + UTILIZATION_SENSITIVITY * unemployment_shock_pp, 0.0, 0.99
    )
    shocked["income"] = np.maximum(
        shocked["income"] * (1 - INCOME_SENSITIVITY * unemployment_shock_pp), 1.0
    )
    shocked["monthly_payment"] = shocked["monthly_payment"] * (1 + PAYMENT_RATE_SENSITIVITY * rate_shock_pp)

    shocked["debt_to_income"] = (shocked["total_debt"] / (shocked["income"] * 12)).round(4)
    shocked["payment_to_income"] = (shocked["monthly_payment"] / shocked["income"]).clip(0, 3).round(4)
    return shocked


def stress_summary(baseline_pd: np.ndarray, stressed_pd: np.ndarray) -> dict:
    return {
        "baseline_avg_pd": round(float(np.mean(baseline_pd)), 4),
        "stressed_avg_pd": round(float(np.mean(stressed_pd)), 4),
        "avg_pd_delta_pp": round(float(np.mean(stressed_pd) - np.mean(baseline_pd)) * 100, 3),
    }
