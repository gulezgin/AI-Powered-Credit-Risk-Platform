import pandas as pd

from src.early_warning.detector import build_signals


def _rows(**overrides):
    """A customer whose position worsened between two monthly snapshots."""
    past = {
        "credit_utilization": 0.30,
        "account_balance": 10_000.0,
        "cumulative_late_payments": 0,
        "cash_withdrawal_count": 10,
    }
    now = {
        "credit_utilization": 0.30,
        "account_balance": 10_000.0,
        "cumulative_late_payments": 0,
        "cash_withdrawal_count": 10,
    }
    now.update(overrides)
    return pd.Series({}), pd.Series(now), pd.Series(past)


def test_signals_are_codes_not_sentences():
    """The dashboard is bilingual, so a signal must carry a code and its numbers
    rather than an English sentence the UI cannot translate."""
    customer, now, past = _rows(credit_utilization=0.55)
    signals = build_signals(customer, now, past)

    assert signals == [{"code": "utilization_up", "params": {"pct": 25}}]


def test_balance_drop_reports_a_positive_percentage():
    customer, now, past = _rows(account_balance=7_500.0)
    signals = build_signals(customer, now, past)

    assert signals == [{"code": "balance_down", "params": {"pct": 25}}]


def test_new_late_payments_are_counted_not_cumulative():
    customer, now, past = _rows(cumulative_late_payments=2)
    signals = build_signals(customer, now, past)

    assert signals == [{"code": "new_late_payments", "params": {"count": 2}}]


def test_quiet_account_raises_nothing():
    customer, now, past = _rows()
    assert build_signals(customer, now, past) == []


def test_several_changes_all_surface():
    customer, now, past = _rows(
        credit_utilization=0.55,
        account_balance=7_500.0,
        cumulative_late_payments=1,
        cash_withdrawal_count=20,
    )
    codes = [s["code"] for s in build_signals(customer, now, past)]

    assert codes == ["utilization_up", "balance_down", "new_late_payments", "withdrawals_up"]
