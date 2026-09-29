from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas import CustomerOut, RiskHistoryPoint
from src.db.database import get_db
from src.db.models import CreditHistory, Customer, RiskPrediction

router = APIRouter(tags=["customers"])


@router.get("/customer/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    latest_pred = db.execute(
        select(RiskPrediction)
        .where(RiskPrediction.customer_id == customer_id)
        .order_by(RiskPrediction.created_at.desc())
    ).scalars().first()

    return CustomerOut(
        customer_id=customer.customer_id, age=customer.age, occupation=customer.occupation,
        income=customer.income, employment_years=customer.employment_years,
        credit_history_years=customer.credit_history_years,
        num_existing_loans=customer.num_existing_loans, total_debt=customer.total_debt,
        credit_utilization=customer.credit_utilization, account_balance=customer.account_balance,
        latest_risk_score=latest_pred.risk_score if latest_pred else None,
        latest_pd=latest_pred.probability_of_default if latest_pred else None,
        latest_risk_level=latest_pred.risk_level if latest_pred else None,
    )


@router.get("/customer/{customer_id}/risk-history", response_model=list[RiskHistoryPoint])
def get_customer_risk_history(customer_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        select(CreditHistory)
        .where(CreditHistory.customer_id == customer_id)
        .order_by(CreditHistory.month_index)
    ).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No history found for customer")
    return [
        RiskHistoryPoint(
            month_index=r.month_index, credit_utilization=r.credit_utilization,
            account_balance=r.account_balance,
        )
        for r in rows
    ]
