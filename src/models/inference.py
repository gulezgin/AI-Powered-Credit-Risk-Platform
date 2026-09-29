"""Single entry point the API (and dashboard) use to go from raw applicant
inputs to a full risk decision: PD -> score -> risk level -> business decision
-> top SHAP drivers."""
from __future__ import annotations

from functools import lru_cache

import joblib
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import MODEL_PATH
from src.decision.engine import evaluate_application
from src.decision.reason_codes import generate_reason_codes
from src.explainability.shap_explainer import explain_customer
from src.features.engineering import ALL_FEATURES, build_behavioral_features
from src.models.scoring import pd_to_score, risk_level


@lru_cache(maxsize=1)
def get_model():
    return joblib.load(MODEL_PATH)


def _derive_ratios(payload: dict) -> dict:
    income = max(payload["income"], 1.0)
    payload = dict(payload)
    payload.setdefault("debt_to_income", round(payload["total_debt"] / (income * 12), 4))
    payload.setdefault("payment_to_income", round(min(payload["monthly_payment"] / income, 3), 4))
    return payload


def score_application(payload: dict) -> dict:
    """payload must contain all NUMERIC_FEATURES (minus the two derived ratios,
    which are computed here) plus `occupation`."""
    payload = _derive_ratios(payload)
    row = pd.DataFrame([{f: payload[f] for f in ALL_FEATURES}])

    model = get_model()
    pd_value = float(model.predict_proba(row)[:, 1][0])
    score = pd_to_score(pd_value)
    level = risk_level(pd_value)

    requested_amount = payload.get("loan_amount", payload["total_debt"])
    decision_info = evaluate_application(pd_value, requested_amount, payload["income"])

    try:
        shap_result = explain_customer(row, top_k=10)
        drivers = shap_result["top_contributors"]
    except Exception:
        drivers = []

    reason_codes = generate_reason_codes(drivers, decision_info["decision"])

    return {
        "probability_of_default": round(pd_value, 4),
        "risk_score": score,
        "risk_level": level,
        "decision": decision_info["decision"],
        "suggested_interest_rate": decision_info["suggested_interest_rate"],
        "approved_amount": decision_info["approved_amount"],
        "key_risk_drivers": [
            {"code": d["code"], "contribution": d["contribution"]} for d in drivers[:5]
        ],
        "reason_codes": reason_codes,
    }


def score_existing_customer(db: Session, customer_id: int, requested_amount: float | None = None) -> dict | None:
    from src.db.models import CreditHistory, Customer, TransactionMonthly

    customer = db.get(Customer, customer_id)
    if not customer:
        return None

    hist_rows = db.execute(
        select(CreditHistory).where(CreditHistory.customer_id == customer_id)
    ).scalars().all()
    txn_rows = db.execute(
        select(TransactionMonthly).where(TransactionMonthly.customer_id == customer_id)
    ).scalars().all()

    hist_df = pd.DataFrame([{
        "customer_id": r.customer_id, "month_index": r.month_index,
        "credit_utilization": r.credit_utilization, "account_balance": r.account_balance,
        "cumulative_late_payments": r.cumulative_late_payments,
    } for r in hist_rows])
    txn_df = pd.DataFrame([{
        "customer_id": r.customer_id, "month_index": r.month_index,
        "cash_withdrawal_count": r.cash_withdrawal_count, "transaction_count": r.transaction_count,
    } for r in txn_rows])
    combined = hist_df.merge(txn_df, on=["customer_id", "month_index"], how="left")
    behavior = build_behavioral_features(combined)
    behavior_row = behavior[behavior["customer_id"] == customer_id]

    payload = {
        "age": customer.age, "occupation": customer.occupation, "income": customer.income,
        "employment_years": customer.employment_years,
        "credit_history_years": customer.credit_history_years,
        "num_existing_loans": customer.num_existing_loans,
        "num_credit_inquiries_6m": customer.num_credit_inquiries_6m,
        "total_debt": customer.total_debt, "monthly_payment": customer.monthly_payment,
        "credit_utilization": customer.credit_utilization,
        "num_late_payments": customer.num_late_payments,
        "account_balance": customer.account_balance,
        "transaction_intensity": customer.transaction_intensity,
        "debt_to_income": customer.debt_to_income, "payment_to_income": customer.payment_to_income,
        "loan_amount": requested_amount or customer.total_debt,
    }
    if not behavior_row.empty:
        b = behavior_row.iloc[0]
        for col in ("utilization_change_30d", "utilization_change_60d", "utilization_change_90d",
                    "balance_change_30d", "balance_change_90d", "withdrawal_change_30d",
                    "late_payments_last_90d"):
            payload[col] = b[col]

    result = score_application(payload)
    result["customer_id"] = customer_id
    return result
