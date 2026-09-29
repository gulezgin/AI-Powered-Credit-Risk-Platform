from src.decision.engine import decide, evaluate_application, suggested_interest_rate
from src.models.scoring import pd_to_score, risk_level


def test_decide_thresholds():
    assert decide(0.01) == "APPROVE"
    assert decide(0.08) == "MANUAL_REVIEW"
    assert decide(0.30) == "REJECT"


def test_interest_rate_increases_with_pd():
    assert suggested_interest_rate(0.02) < suggested_interest_rate(0.10)


def test_evaluate_application_rejects_zero_amount():
    result = evaluate_application(pd_value=0.5, requested_amount=100000, income=10000)
    assert result["decision"] == "REJECT"
    assert result["approved_amount"] == 0.0


def test_pd_to_score_monotonic():
    assert pd_to_score(0.01) > pd_to_score(0.20)


def test_risk_level_buckets():
    assert risk_level(0.01) == "LOW"
    assert risk_level(0.08) == "MEDIUM"
    assert risk_level(0.20) == "HIGH"
    assert risk_level(0.40) == "CRITICAL"
