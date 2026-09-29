from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import CreditDecisionRequest, CreditDecisionResponse
from src.db.database import get_db
from src.models.inference import score_existing_customer

router = APIRouter(tags=["decisions"])


@router.post("/credit-decision", response_model=CreditDecisionResponse)
def credit_decision(payload: CreditDecisionRequest, db: Session = Depends(get_db)):
    result = score_existing_customer(db, payload.customer_id, payload.requested_amount)
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    result["approved_amount"] = result["approved_amount"] or 0.0
    return result
