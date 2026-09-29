"""Business decision layer, kept separate from the ML model on purpose:
credit policy (thresholds, pricing) changes on a business cadence and must be
auditable/overridable without retraining anything.

Thresholds live in a `CreditPolicy` rather than as module constants because a
cut-off is only meaningful relative to a portfolio's base default rate — the
synthetic book defaults at ~7% and the real UCI card book at ~22%, so the same
5%/12% cut-offs would reject nearly everyone on the latter.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import PD_APPROVE_THRESHOLD, PD_REVIEW_THRESHOLD


@dataclass(frozen=True)
class CreditPolicy:
    approve_below: float
    review_below: float
    base_rate: float = 0.018  # policy floor interest rate
    risk_premium_per_pd_unit: float = 0.28
    max_rate: float = 0.65


DEFAULT_POLICY = CreditPolicy(
    approve_below=PD_APPROVE_THRESHOLD,
    review_below=PD_REVIEW_THRESHOLD,
)

# Calibrated to the real UCI card portfolio's ~22% base default rate.
UCI_POLICY = CreditPolicy(approve_below=0.15, review_below=0.30)

POLICIES = {"synthetic": DEFAULT_POLICY, "uci": UCI_POLICY}


def decide(pd_value: float, policy: CreditPolicy = DEFAULT_POLICY) -> str:
    if pd_value < policy.approve_below:
        return "APPROVE"
    if pd_value < policy.review_below:
        return "MANUAL_REVIEW"
    return "REJECT"


def suggested_interest_rate(pd_value: float, policy: CreditPolicy = DEFAULT_POLICY) -> float:
    rate = policy.base_rate + policy.risk_premium_per_pd_unit * pd_value
    return round(min(rate, policy.max_rate), 4)


def suggested_loan_amount(
    requested_amount: float, income: float, pd_value: float, policy: CreditPolicy = DEFAULT_POLICY
) -> float:
    """Caps the approved amount for higher-risk borrowers instead of a flat reject,
    a common real-world middle ground between full approval and rejection."""
    if pd_value >= policy.review_below:
        return 0.0
    max_by_income = income * 12 * (2.5 if pd_value < policy.approve_below else 1.2)
    return round(min(requested_amount, max_by_income), 2)


def evaluate_application(
    pd_value: float, requested_amount: float, income: float,
    policy: CreditPolicy = DEFAULT_POLICY,
) -> dict:
    decision = decide(pd_value, policy)
    approved_amount = (
        suggested_loan_amount(requested_amount, income, pd_value, policy)
        if decision != "REJECT" else 0.0
    )
    return {
        "decision": decision,
        "suggested_interest_rate": suggested_interest_rate(pd_value, policy) if decision != "REJECT" else None,
        "approved_amount": approved_amount,
    }
