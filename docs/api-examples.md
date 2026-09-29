# API examples

Real responses from a running instance, not hand-written illustrations. Figures
move when the model is retrained; the shapes do not.

## Score an application — `POST /predict-risk`

```json
{
  "age": 45, "occupation": "Retail Worker", "income": 15000,
  "employment_years": 0.5, "credit_history_years": 1,
  "num_existing_loans": 5, "num_credit_inquiries_6m": 8,
  "total_debt": 400000, "monthly_payment": 13000,
  "credit_utilization": 0.95, "num_late_payments": 9,
  "account_balance": 500, "transaction_intensity": 5,
  "loan_amount": 100000
}
```

```json
{
  "risk_score": 300,
  "probability_of_default": 1.0,
  "risk_level": "CRITICAL",
  "decision": "REJECT",
  "suggested_interest_rate": null,
  "approved_amount": 0.0,
  "key_risk_drivers": [
    { "code": "debt_to_income", "contribution": 0.3416 },
    { "code": "num_late_payments", "contribution": 0.2362 },
    { "code": "credit_utilization", "contribution": 0.0876 },
    { "code": "num_credit_inquiries_6m", "contribution": 0.0845 },
    { "code": "total_debt", "contribution": 0.065 }
  ],
  "reason_codes": [
    "dti_too_high",
    "delinquent_obligations",
    "revolving_utilisation_too_high",
    "too_many_recent_inquiries"
  ]
}
```

The dashboard renders that as "Debt is too high relative to income" in English
and "Borç, gelire göre fazla yüksek" in Turkish. `reason_codes` is empty on
`APPROVE` and populated only on `MANUAL_REVIEW` / `REJECT`, mirroring when an
adverse action notice is actually owed.

A well-qualified applicant on the same endpoint:

```json
{
  "risk_score": 850,
  "probability_of_default": 0.0056,
  "risk_level": "LOW",
  "decision": "APPROVE",
  "suggested_interest_rate": 0.0196,
  "approved_amount": 250000.0,
  "key_risk_drivers": [
    { "code": "income", "contribution": -0.1479 },
    { "code": "total_debt", "contribution": 0.0601 },
    { "code": "debt_to_income", "contribution": -0.0536 },
    { "code": "credit_utilization", "contribution": 0.0282 },
    { "code": "num_credit_inquiries_6m", "contribution": 0.0267 }
  ],
  "reason_codes": []
}
```

Negative contributions pull the estimate down. They sum with the model's base
rate to the reported `probability_of_default`, because the explainer runs
against the calibrated pipeline rather than the raw estimator underneath it.

## Watchlist — `GET /alerts`

```json
{
  "customer_id": 18899,
  "previous_risk_level": "HIGH",
  "current_risk_level": "CRITICAL",
  "previous_pd": 0.2005,
  "current_pd": 0.3229,
  "signals": [
    { "code": "balance_down", "params": { "pct": 18.0 } },
    { "code": "new_late_payments", "params": { "count": 1.0 } },
    { "code": "withdrawals_up", "params": { "pct": 67.0 } }
  ],
  "recommended_action": "immediate_review"
}
```

This is not a threshold rule on one field. The same PD model is scored at two
points in the account's history, so "risk rose" means the model's own estimate
crossed a band — here from 20.1% to 32.3%. The signals explain what changed
underneath it.
