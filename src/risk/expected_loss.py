"""Expected Credit Loss, IFRS 9 / CECL style: EL = PD x LGD x EAD.

LGD (Loss Given Default) defaults to 45%, the Basel II Foundation-IRB
supervisory value for senior unsecured retail exposure — a defensible
placeholder in the absence of a bank's own recovery-rate history. EAD
(Exposure At Default) is approximated as outstanding total_debt, which is
standard for revolving/term retail credit without an undrawn-commitment
component.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_LGD = 0.45


def expected_loss(pd_value: float, ead: float, lgd: float = DEFAULT_LGD) -> float:
    return max(0.0, pd_value) * lgd * max(0.0, ead)


def portfolio_expected_loss(df: pd.DataFrame, pd_col: str = "probability_of_default",
                             ead_col: str = "total_debt", lgd: float = DEFAULT_LGD) -> dict:
    """df needs one row per customer with a PD column and an EAD column."""
    el = df[pd_col].clip(lower=0) * lgd * df[ead_col].clip(lower=0)
    total_exposure = float(df[ead_col].sum())
    total_el = float(el.sum())

    by_risk_level = {}
    if "risk_level" in df.columns:
        grouped = df.assign(_el=el).groupby("risk_level")["_el"].sum()
        by_risk_level = {k: round(float(v), 2) for k, v in grouped.items()}

    return {
        "lgd_assumption": lgd,
        "total_exposure": round(total_exposure, 2),
        "total_expected_loss": round(total_el, 2),
        "expected_loss_ratio": round(total_el / total_exposure, 5) if total_exposure > 0 else 0.0,
        "expected_loss_by_risk_level": by_risk_level,
        "n_accounts": int(len(df)),
    }
