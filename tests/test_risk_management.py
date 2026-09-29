import pandas as pd
import pytest

from src.decision.reason_codes import generate_reason_codes
from src.monitoring.fairness import group_disparity
from src.risk.expected_loss import expected_loss, portfolio_expected_loss
from src.risk.stress_test import apply_macro_shock, stress_summary


def test_reason_codes_empty_on_approve():
    drivers = [{"code": "debt_to_income", "contribution": 0.3}]
    assert generate_reason_codes(drivers, "APPROVE") == []


def test_reason_codes_exclude_protected_features():
    """ECOA: age is protected and occupation proxies for protected classes, so
    neither may appear on a notice even when the model leans on them."""
    drivers = [
        {"code": "age", "contribution": 0.4},
        {"code": "occupation", "contribution": 0.3},
        {"code": "debt_to_income", "contribution": 0.2},
    ]
    assert generate_reason_codes(drivers, "REJECT") == ["dti_too_high"]


def test_reason_codes_are_grounds_not_sentences():
    """The notice is served in the applicant's language, so the API states the
    ground as a code and the wording is chosen at presentation."""
    drivers = [{"code": "credit_utilization", "contribution": 0.2}]
    grounds = generate_reason_codes(drivers, "REJECT")

    assert grounds == ["revolving_utilisation_too_high"]
    assert all(" " not in g for g in grounds)


def test_reason_codes_state_each_ground_once():
    """Several features map to the same ground; the applicant hears it once."""
    drivers = [
        {"code": "utilization_change_30d", "contribution": 0.3},
        {"code": "utilization_change_60d", "contribution": 0.2},
        {"code": "utilization_change_90d", "contribution": 0.1},
    ]
    assert generate_reason_codes(drivers, "REJECT") == ["utilisation_rising"]


def test_reason_codes_ignore_protective_factors():
    drivers = [{"code": "income", "contribution": -0.5}]
    assert generate_reason_codes(drivers, "MANUAL_REVIEW") == []


def test_expected_loss_formula():
    assert expected_loss(pd_value=0.1, ead=100000, lgd=0.45) == pytest.approx(4500.0)


def test_portfolio_expected_loss_ratio():
    df = pd.DataFrame({
        "probability_of_default": [0.1, 0.2],
        "total_debt": [100000, 200000],
        "risk_level": ["LOW", "HIGH"],
    })
    result = portfolio_expected_loss(df)
    assert result["total_exposure"] == pytest.approx(300000)
    assert result["total_expected_loss"] == pytest.approx(0.45 * (0.1 * 100000 + 0.2 * 200000))
    assert result["n_accounts"] == 2


def test_macro_shock_increases_risk_inputs():
    df = pd.DataFrame({
        "credit_utilization": [0.5], "income": [10000], "monthly_payment": [1000],
        "total_debt": [50000],
    })
    shocked = apply_macro_shock(df, unemployment_shock_pp=2, rate_shock_pp=1)
    assert shocked["credit_utilization"].iloc[0] > df["credit_utilization"].iloc[0]
    assert shocked["income"].iloc[0] < df["income"].iloc[0]
    assert shocked["monthly_payment"].iloc[0] > df["monthly_payment"].iloc[0]


def test_stress_summary_direction():
    import numpy as np
    baseline = np.array([0.05, 0.05])
    stressed = np.array([0.08, 0.08])
    summary = stress_summary(baseline, stressed)
    assert summary["avg_pd_delta_pp"] > 0


def test_group_disparity_flags_low_ratio():
    df = pd.DataFrame({
        "occupation": ["A"] * 10 + ["B"] * 10,
        "decision": ["APPROVE"] * 9 + ["REJECT"] * 1 + ["APPROVE"] * 5 + ["REJECT"] * 5,
        "probability_of_default": [0.05] * 10 + [0.15] * 10,
    })
    result = group_disparity(df, min_group_size=1)
    row_b = result[result["occupation"] == "B"].iloc[0]
    assert row_b["flagged"] == True
    assert row_b["adverse_impact_ratio"] == pytest.approx(5 / 9, abs=1e-3)


def test_group_disparity_ignores_tiny_group_as_reference():
    """A 3-person group with a 100% approval rate must not become the yardstick
    that flags everyone else — the four-fifths rule is unreliable at that size."""
    df = pd.DataFrame({
        "occupation": ["Big"] * 600 + ["Tiny"] * 3,
        "decision": (["APPROVE"] * 480 + ["REJECT"] * 120) + ["APPROVE"] * 3,
        "probability_of_default": [0.1] * 603,
    })
    result = group_disparity(df, min_group_size=500)

    big = result[result["occupation"] == "Big"].iloc[0]
    tiny = result[result["occupation"] == "Tiny"].iloc[0]
    assert big["adverse_impact_ratio"] == pytest.approx(1.0)
    assert not big["flagged"]
    assert tiny["insufficient_sample"]
    assert not tiny["flagged"]
