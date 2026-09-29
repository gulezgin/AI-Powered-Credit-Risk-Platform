import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.config import MODEL_PATH

client = TestClient(app)

pytestmark = pytest.mark.skipif(
    not MODEL_PATH.exists(), reason="Model not trained yet — run scripts/run_pipeline.py first"
)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_predict_risk():
    payload = {
        "age": 34, "occupation": "Engineer", "income": 85000,
        "employment_years": 3, "credit_history_years": 6,
        "num_existing_loans": 2, "num_credit_inquiries_6m": 3,
        "total_debt": 310000, "monthly_payment": 9800,
        "credit_utilization": 0.72, "num_late_payments": 2,
        "account_balance": 42000, "transaction_intensity": 35,
        "loan_amount": 250000,
    }
    resp = client.post("/predict-risk", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["probability_of_default"] <= 1
    assert body["decision"] in ("APPROVE", "MANUAL_REVIEW", "REJECT")
    assert 300 <= body["risk_score"] <= 850


def test_predict_risk_rejects_invalid_utilization():
    payload = {
        "age": 34, "occupation": "Engineer", "income": 85000,
        "employment_years": 3, "credit_history_years": 6,
        "num_existing_loans": 2, "num_credit_inquiries_6m": 3,
        "total_debt": 310000, "monthly_payment": 9800,
        "credit_utilization": 1.5, "num_late_payments": 2,
        "account_balance": 42000, "transaction_intensity": 35,
        "loan_amount": 250000,
    }
    resp = client.post("/predict-risk", json=payload)
    assert resp.status_code == 422
