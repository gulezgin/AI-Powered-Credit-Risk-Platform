import pandas as pd
import pytest

from src.datasets import uci_credit


@pytest.fixture
def fake_raw():
    """Two customers with hand-picked values so the point-in-time index maths is
    checkable by hand. Raw columns are most-recent-first (BILL_AMT1 = September)."""
    return pd.DataFrame({
        "ID": [1, 2],
        "LIMIT_BAL": [100_000, 200_000],
        "SEX": [1, 2],
        "EDUCATION": [1, 3],
        "MARRIAGE": [1, 2],
        "AGE": [30, 45],
        # Sep, Aug, Jul, Jun, May, Apr
        "PAY_0": [2, 0], "PAY_2": [1, 0], "PAY_3": [0, 0],
        "PAY_4": [0, -1], "PAY_5": [-1, -1], "PAY_6": [-2, -2],
        "BILL_AMT1": [50_000, 20_000], "BILL_AMT2": [40_000, 22_000],
        "BILL_AMT3": [30_000, 24_000], "BILL_AMT4": [20_000, 26_000],
        "BILL_AMT5": [10_000, 28_000], "BILL_AMT6": [5_000, 30_000],
        "PAY_AMT1": [1_000, 5_000], "PAY_AMT2": [2_000, 5_000],
        "PAY_AMT3": [3_000, 5_000], "PAY_AMT4": [4_000, 5_000],
        "PAY_AMT5": [5_000, 5_000], "PAY_AMT6": [6_000, 5_000],
        "default payment next month": [1, 0],
    })


def test_current_features_use_latest_month(fake_raw):
    df = uci_credit.build_customers(fake_raw)
    c1 = df.iloc[0]

    assert c1["credit_utilization"] == pytest.approx(0.5)      # 50k / 100k
    assert c1["current_balance"] == pytest.approx(50_000)
    assert c1["last_payment"] == pytest.approx(1_000)
    # Sep(2) + Aug(1) are the only delinquent months
    assert c1["num_late_payments"] == 2
    assert c1["max_delinquency"] == 2


def test_trend_features_measure_real_movement(fake_raw):
    df = uci_credit.build_customers(fake_raw)
    rising, falling = df.iloc[0], df.iloc[1]

    # Customer 1's balance climbs 5k -> 50k, so every window is positive.
    assert rising["utilization_change_30d"] == pytest.approx(0.1)   # 0.5 - 0.4
    assert rising["utilization_change_90d"] == pytest.approx(0.3)   # 0.5 - 0.2
    assert rising["balance_change_30d"] > 0
    # Customer 2 is paying down, so utilization trends negative.
    assert falling["utilization_change_90d"] < 0


def test_as_of_index_rebuilds_the_past(fake_raw):
    """Chronological index 3 is July (BILL_AMT3), so the frame must show July's
    view of the customer, not September's."""
    past = uci_credit.build_customers(fake_raw, as_of_index=3)
    c1 = past.iloc[0]

    assert c1["credit_utilization"] == pytest.approx(0.3)   # BILL_AMT3 = 30k / 100k
    assert c1["current_balance"] == pytest.approx(30_000)
    # Apr/May/Jun/Jul carry no delinquency for this customer; the 2 late months
    # (Aug, Sep) are in the future relative to this as-of date.
    assert c1["num_late_payments"] == 0


def test_as_of_index_is_bounded(fake_raw):
    with pytest.raises(ValueError):
        uci_credit.build_customers(fake_raw, as_of_index=2)


def test_protected_attributes_are_not_model_features():
    """ECOA: sex and marital status must never be a basis for the decision."""
    for attr in uci_credit.PROTECTED_ATTRIBUTES:
        assert attr not in uci_credit.ALL_FEATURES


def test_history_is_chronological_and_complete(fake_raw):
    hist = uci_credit.build_history(fake_raw)
    assert len(hist) == 12  # 2 customers x 6 months

    c1 = hist[hist["customer_id"] == 1].sort_values("month_index")
    # month_index 0 is the oldest month (April = BILL_AMT6)
    assert c1.iloc[0]["bill_amount"] == pytest.approx(5_000)
    assert c1.iloc[-1]["bill_amount"] == pytest.approx(50_000)
    assert list(c1["cumulative_late_payments"]) == [0, 0, 0, 0, 1, 2]
