from datetime import datetime

from pydantic import BaseModel, Field


class PredictRiskRequest(BaseModel):
    age: int = Field(ge=18, le=100)
    occupation: str
    income: float = Field(gt=0)
    employment_years: float = Field(ge=0)
    credit_history_years: float = Field(ge=0)
    num_existing_loans: int = Field(ge=0)
    num_credit_inquiries_6m: int = Field(ge=0)
    total_debt: float = Field(ge=0)
    monthly_payment: float = Field(ge=0)
    credit_utilization: float = Field(ge=0, le=1)
    num_late_payments: int = Field(ge=0)
    account_balance: float = Field(ge=0)
    transaction_intensity: float = Field(ge=0)
    loan_amount: float = Field(gt=0, description="Requested loan amount")
    utilization_change_30d: float = 0.0
    utilization_change_60d: float = 0.0
    utilization_change_90d: float = 0.0
    balance_change_30d: float = 0.0
    balance_change_90d: float = 0.0
    withdrawal_change_30d: float = 0.0
    late_payments_last_90d: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "age": 34, "occupation": "Engineer", "income": 85000,
                "employment_years": 3, "credit_history_years": 6,
                "num_existing_loans": 2, "num_credit_inquiries_6m": 3,
                "total_debt": 310000, "monthly_payment": 9800,
                "credit_utilization": 0.72, "num_late_payments": 2,
                "account_balance": 42000, "transaction_intensity": 35,
                "loan_amount": 250000,
            }
        }


class RiskDriver(BaseModel):
    """A model feature and how much it moved this applicant's estimate. `code`
    is the feature name; the dashboard turns it into a label per locale."""

    code: str
    contribution: float


class PredictRiskResponse(BaseModel):
    risk_score: int
    probability_of_default: float
    risk_level: str
    decision: str
    suggested_interest_rate: float | None
    approved_amount: float | None
    key_risk_drivers: list[RiskDriver]
    reason_codes: list[str] = Field(
        default_factory=list,
        description=(
            "ECOA/Reg B adverse action grounds as codes, populated when decision "
            "!= APPROVE. The notice wording is rendered in the applicant's language."
        ),
    )


class CustomerOut(BaseModel):
    customer_id: int
    age: int
    occupation: str
    income: float
    employment_years: float
    credit_history_years: float
    num_existing_loans: int
    total_debt: float
    credit_utilization: float
    account_balance: float
    latest_risk_score: int | None = None
    latest_pd: float | None = None
    latest_risk_level: str | None = None


class RiskHistoryPoint(BaseModel):
    month_index: int
    credit_utilization: float
    account_balance: float


class Signal(BaseModel):
    """A detected change, as a code plus its numbers. The dashboard turns it
    into a sentence in the reader's language."""

    code: str
    params: dict[str, float] = Field(default_factory=dict)


class AlertOut(BaseModel):
    id: int
    customer_id: int
    previous_risk_level: str
    current_risk_level: str
    previous_pd: float
    current_pd: float
    signals: list[Signal]
    recommended_action: str
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CreditDecisionRequest(BaseModel):
    customer_id: int
    requested_amount: float = Field(gt=0)


class CreditDecisionResponse(BaseModel):
    customer_id: int
    probability_of_default: float
    risk_score: int
    risk_level: str
    decision: str
    suggested_interest_rate: float | None
    approved_amount: float
    key_risk_drivers: list[RiskDriver]
    reason_codes: list[str] = Field(default_factory=list)
