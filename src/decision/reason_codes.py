"""Adverse Action reason codes — the standardized grounds a U.S. lender must
give an applicant under ECOA/Regulation B when credit is denied or priced worse
than the best terms (12 CFR 1002.9). They are derived from the SHAP drivers
that raised this applicant's PD the most, so the stated grounds are the model's
actual grounds rather than a separate rule set.

The API emits a code per ground, not a finished sentence: the notice has to be
served in the applicant's language, so the wording is chosen at the point of
presentation. The mapping from model feature to ground stays here, because
*which* ground applies is a credit-policy decision and belongs with the model.

`age` and `occupation` are deliberately excluded even when they show up as SHAP
drivers: age is a protected characteristic under ECOA, and occupation is a
plausible proxy for protected classes, so neither may appear on a notice.
"""
from __future__ import annotations

EXCLUDED_FROM_NOTICE = {"age", "occupation"}

# Model feature -> adverse action ground. Several features can map to the same
# ground; an applicant is told each ground once.
REASON_CODE_MAP = {
    "debt_to_income": "dti_too_high",
    "payment_to_income": "payment_burden_too_high",
    "credit_utilization": "revolving_utilisation_too_high",
    "num_late_payments": "delinquent_obligations",
    "late_payments_last_90d": "recent_delinquency",
    "num_credit_inquiries_6m": "too_many_recent_inquiries",
    "credit_history_years": "credit_history_too_short",
    "employment_years": "employment_too_short",
    "num_existing_loans": "too_many_obligations",
    "account_balance": "insufficient_reserves",
    "income": "income_insufficient_for_amount",
    "total_debt": "amount_owed_too_high",
    "monthly_payment": "monthly_obligations_too_high",
    "transaction_intensity": "insufficient_account_activity",
    "utilization_change_30d": "utilisation_rising",
    "utilization_change_60d": "utilisation_rising",
    "utilization_change_90d": "utilisation_rising",
    "balance_change_30d": "balance_falling",
    "balance_change_90d": "balance_falling",
    "withdrawal_change_30d": "cash_withdrawals_rising",
}

MAX_REASON_CODES = 4


def generate_reason_codes(top_contributors: list[dict], decision: str) -> list[str]:
    """top_contributors: SHAP driver dicts with `code` and `contribution`
    (positive contribution = increases probability of default)."""
    if decision == "APPROVE":
        return []

    risk_increasing = [
        d for d in top_contributors
        if d.get("contribution", 0) > 0 and d.get("code") not in EXCLUDED_FROM_NOTICE
    ]
    risk_increasing.sort(key=lambda d: d["contribution"], reverse=True)

    grounds: list[str] = []
    for d in risk_increasing:
        ground = REASON_CODE_MAP.get(d["code"])
        if ground and ground not in grounds:
            grounds.append(ground)
        if len(grounds) >= MAX_REASON_CODES:
            break
    return grounds
