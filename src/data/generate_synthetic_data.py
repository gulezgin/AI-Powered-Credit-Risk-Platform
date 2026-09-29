"""Synthetic bank credit-risk dataset generator.

Produces a causally-structured dataset (not pure noise): default risk is
driven by a weighted combination of debt burden, utilization, payment
history, tenure and inquiry behavior, run through a logistic link. A subset
of customers is seeded with a deteriorating 12-month behavioral trend so the
early-warning system has real signal to detect.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import DATA_RAW_DIR, HISTORY_MONTHS, N_CUSTOMERS, RANDOM_SEED

OCCUPATIONS = [
    "Engineer", "Teacher", "Civil Servant", "Business Owner", "Healthcare Worker",
    "Retail Worker", "Driver", "Accountant", "IT Specialist", "Retired",
]
OCCUPATION_INCOME_MULT = {
    "Engineer": 1.35, "Teacher": 0.85, "Civil Servant": 0.95, "Business Owner": 1.5,
    "Healthcare Worker": 1.15, "Retail Worker": 0.75, "Driver": 0.7,
    "Accountant": 1.1, "IT Specialist": 1.45, "Retired": 0.6,
}


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def _zscore(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / (x.std() + 1e-9)


def generate_customers(n: int, rng: np.random.Generator) -> pd.DataFrame:
    customer_id = np.arange(10001, 10001 + n)

    age = np.clip(rng.normal(38, 11, n), 18, 80).round().astype(int)
    occupation = rng.choice(OCCUPATIONS, size=n)
    income_mult = np.array([OCCUPATION_INCOME_MULT[o] for o in occupation])
    base_income = rng.lognormal(mean=9.9, sigma=0.45, size=n)  # ~ TL/month
    income = np.clip(base_income * income_mult, 8000, 400000).round(2)

    employment_years = np.clip(
        rng.gamma(shape=2.0, scale=(age - 17).clip(min=1) / 9, size=n), 0, age - 17
    ).round(1)
    credit_history_years = np.clip(
        employment_years * rng.uniform(0.6, 1.3, n) + rng.normal(0, 1, n), 0, age - 16
    ).round(1)

    num_existing_loans = rng.poisson(1.1, n).clip(0, 8)
    num_credit_inquiries_6m = rng.poisson(0.8, n).clip(0, 10)

    credit_utilization = np.clip(rng.beta(2.0, 3.5, n) + rng.normal(0, 0.05, n), 0.01, 0.99)

    total_debt = np.clip(
        income * rng.uniform(1.5, 9.0, n) * (0.4 + credit_utilization), 0, None
    ).round(2)
    monthly_payment = np.clip(total_debt * rng.uniform(0.02, 0.09, n), 0, income * 0.9).round(2)

    num_late_payments = rng.poisson(
        0.4 + 2.2 * credit_utilization + 0.15 * num_credit_inquiries_6m, n
    ).clip(0, 24)

    account_balance = np.clip(
        income * rng.uniform(0.2, 3.0, n) * (1 - 0.5 * credit_utilization), 0, None
    ).round(2)
    transaction_intensity = rng.poisson(18 + income / 6000, n).clip(1, 200)

    df = pd.DataFrame({
        "customer_id": customer_id,
        "age": age,
        "occupation": occupation,
        "income": income,
        "employment_years": employment_years,
        "credit_history_years": credit_history_years,
        "num_existing_loans": num_existing_loans,
        "num_credit_inquiries_6m": num_credit_inquiries_6m,
        "total_debt": total_debt,
        "monthly_payment": monthly_payment,
        "credit_utilization": credit_utilization.round(4),
        "num_late_payments": num_late_payments,
        "account_balance": account_balance,
        "transaction_intensity": transaction_intensity,
    })
    df["debt_to_income"] = (df["total_debt"] / (df["income"] * 12)).round(4)
    df["payment_to_income"] = (df["monthly_payment"] / df["income"]).clip(0, 3).round(4)
    return df


def assign_default_labels(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    z_dti = _zscore(df["debt_to_income"].values)
    z_util = _zscore(df["credit_utilization"].values)
    z_late = _zscore(df["num_late_payments"].values)
    z_inq = _zscore(df["num_credit_inquiries_6m"].values)
    z_emp = _zscore(df["employment_years"].values)
    z_hist = _zscore(df["credit_history_years"].values)
    z_income = _zscore(np.log1p(df["income"].values))
    z_pti = _zscore(df["payment_to_income"].values)

    logit = (
        -4.5
        + 0.85 * z_dti
        + 0.70 * z_util
        + 0.55 * z_late
        + 0.30 * z_inq
        + 0.40 * z_pti
        - 0.45 * z_emp
        - 0.35 * z_hist
        - 0.30 * z_income
        + 0.25 * z_dti * z_util  # over-leveraged AND maxed-out compounds risk
        + rng.normal(0, 0.55, len(df))  # idiosyncratic noise
    )
    pd_true = _sigmoid(logit)
    default = rng.binomial(1, pd_true)

    df = df.copy()
    df["true_pd"] = pd_true.round(6)
    df["default"] = default
    return df


def generate_credit_history(df: pd.DataFrame, months: int, rng: np.random.Generator) -> pd.DataFrame:
    """Monthly behavioral snapshots per customer, feeding the early-warning engine.

    ~18% of customers are seeded with a deteriorating trend in the most recent
    3-4 months (rising utilization/withdrawals, fresh late payments) regardless
    of their static label, mirroring real accounts whose risk is *emerging*.
    """
    n = len(df)
    deteriorating = rng.random(n) < 0.18
    improving = (~deteriorating) & (rng.random(n) < 0.10)

    records = []
    base_util = df["credit_utilization"].values
    base_balance = df["account_balance"].values
    base_txn = df["transaction_intensity"].values

    for i, cust_id in enumerate(df["customer_id"].values):
        util = base_util[i]
        balance = base_balance[i]
        txn = base_txn[i]
        withdrawals = max(1, int(txn * rng.uniform(0.15, 0.35)))
        cumulative_late = 0

        drift_start = months - rng.integers(3, 5)

        for m in range(months):
            noise_util = rng.normal(0, 0.015)
            noise_bal = rng.normal(0, 0.03)

            if deteriorating[i] and m >= drift_start:
                step = (m - drift_start + 1) / (months - drift_start)
                util = np.clip(util + step * rng.uniform(0.06, 0.14) + noise_util, 0.01, 0.99)
                balance = max(0.0, balance * (1 - step * rng.uniform(0.05, 0.12)) + noise_bal * balance)
                withdrawals = withdrawals * (1 + step * rng.uniform(0.15, 0.35))
                if rng.random() < 0.35 * step:
                    cumulative_late += 1
            elif improving[i] and m >= drift_start:
                step = (m - drift_start + 1) / (months - drift_start)
                util = np.clip(util - step * rng.uniform(0.04, 0.10) + noise_util, 0.01, 0.99)
                balance = max(0.0, balance * (1 + step * rng.uniform(0.03, 0.08)) + noise_bal * balance)
                withdrawals = max(1.0, withdrawals * (1 - step * rng.uniform(0.05, 0.15)))
            else:
                util = np.clip(util + noise_util, 0.01, 0.99)
                balance = max(0.0, balance + noise_bal * balance)

            records.append({
                "customer_id": cust_id,
                "month_index": m,
                "credit_utilization": round(float(util), 4),
                "account_balance": round(float(balance), 2),
                "cumulative_late_payments": int(cumulative_late),
                "cash_withdrawal_count": int(round(withdrawals)),
                "transaction_count": int(max(1, round(txn + rng.normal(0, 3)))),
            })

    hist = pd.DataFrame.from_records(records)
    hist["is_deteriorating_seed"] = hist["customer_id"].isin(
        df.loc[deteriorating, "customer_id"]
    )
    return hist


def generate_loans(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    loan_records = []
    loan_id = 500001
    for _, row in df.iterrows():
        n_loans = max(1, int(row["num_existing_loans"]))
        remaining_debt = row["total_debt"]
        for j in range(n_loans):
            amount = remaining_debt / (n_loans - j) if (n_loans - j) > 0 else remaining_debt
            amount = max(1000.0, amount * rng.uniform(0.7, 1.3))
            remaining_debt = max(0.0, remaining_debt - amount)
            loan_records.append({
                "loan_id": loan_id,
                "customer_id": row["customer_id"],
                "loan_amount": round(amount, 2),
                "term_months": int(rng.choice([12, 24, 36, 48, 60])),
                "interest_rate": round(float(rng.uniform(0.018, 0.045)), 4),
                "status": "ACTIVE",
            })
            loan_id += 1
    return pd.DataFrame(loan_records)


def main():
    rng = np.random.default_rng(RANDOM_SEED)

    customers = generate_customers(N_CUSTOMERS, rng)
    customers = assign_default_labels(customers, rng)
    credit_history = generate_credit_history(customers, HISTORY_MONTHS, rng)
    loans = generate_loans(customers, rng)

    customers.to_csv(DATA_RAW_DIR / "customers.csv", index=False)
    credit_history.to_csv(DATA_RAW_DIR / "credit_history.csv", index=False)
    loans.to_csv(DATA_RAW_DIR / "loans.csv", index=False)

    print(f"customers: {customers.shape}, default_rate={customers['default'].mean():.4f}")
    print(f"credit_history: {credit_history.shape}")
    print(f"loans: {loans.shape}")
    print(f"Saved to {DATA_RAW_DIR}")


if __name__ == "__main__":
    main()
