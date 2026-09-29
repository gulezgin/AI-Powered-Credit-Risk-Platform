"""Load generated CSVs + trained model artifacts into the database:
customers, loans, credit_history, transactions, an initial risk_predictions
snapshot for every customer, seeded risk_alerts, and the active model_version row."""
from __future__ import annotations

import joblib
import pandas as pd
from sqlalchemy import text

from src.config import DATA_RAW_DIR, METRICS_PATH, MODEL_PATH
from src.db.database import Base, SessionLocal, engine
from src.db.models import (
    Customer,
    CreditHistory,
    Loan,
    ModelVersion,
    RiskAlert,
    RiskPrediction,
    TransactionMonthly,
)
from src.decision.engine import evaluate_application
from src.early_warning.detector import scan_for_alerts
from src.explainability.shap_explainer import explain_customer
from src.features.engineering import ALL_FEATURES, build_training_frame
from src.models.scoring import pd_to_score, risk_level
import json


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed(limit_alerts_scan: int = 3000):
    customers = pd.read_csv(DATA_RAW_DIR / "customers.csv")
    history = pd.read_csv(DATA_RAW_DIR / "credit_history.csv")
    loans = pd.read_csv(DATA_RAW_DIR / "loans.csv")
    model = joblib.load(MODEL_PATH)

    with open(METRICS_PATH) as f:
        metrics = json.load(f)
    champion = metrics["champion_model"]
    champ_metrics = metrics["comparison"][f"{champion}_calibrated"]

    reset_db()
    db = SessionLocal()
    try:
        db.execute(text("PRAGMA foreign_keys=OFF") if engine.url.get_backend_name() == "sqlite" else text("SELECT 1"))

        db.bulk_insert_mappings(Customer, [
            {
                "customer_id": int(r.customer_id), "age": int(r.age), "occupation": r.occupation,
                "income": float(r.income), "employment_years": float(r.employment_years),
                "credit_history_years": float(r.credit_history_years),
                "num_existing_loans": int(r.num_existing_loans),
                "num_credit_inquiries_6m": int(r.num_credit_inquiries_6m),
                "total_debt": float(r.total_debt), "monthly_payment": float(r.monthly_payment),
                "credit_utilization": float(r.credit_utilization),
                "num_late_payments": int(r.num_late_payments),
                "account_balance": float(r.account_balance),
                "transaction_intensity": float(r.transaction_intensity),
                "debt_to_income": float(r.debt_to_income), "payment_to_income": float(r.payment_to_income),
                "ground_truth_default": int(r.default),
            }
            for r in customers.itertuples()
        ])
        db.commit()

        db.bulk_insert_mappings(Loan, [
            {
                "loan_id": int(r.loan_id), "customer_id": int(r.customer_id),
                "loan_amount": float(r.loan_amount), "term_months": int(r.term_months),
                "interest_rate": float(r.interest_rate), "status": r.status,
            }
            for r in loans.itertuples()
        ])
        db.commit()

        db.bulk_insert_mappings(CreditHistory, [
            {
                "customer_id": int(r.customer_id), "month_index": int(r.month_index),
                "credit_utilization": float(r.credit_utilization),
                "account_balance": float(r.account_balance),
                "cumulative_late_payments": int(r.cumulative_late_payments),
            }
            for r in history.itertuples()
        ])
        db.commit()

        db.bulk_insert_mappings(TransactionMonthly, [
            {
                "customer_id": int(r.customer_id), "month_index": int(r.month_index),
                "transaction_count": int(r.transaction_count),
                "cash_withdrawal_count": int(r.cash_withdrawal_count),
            }
            for r in history.itertuples()
        ])
        db.commit()

        db.add(ModelVersion(
            version_name="v1.0.0",
            champion_model=champion,
            roc_auc=champ_metrics["roc_auc"],
            pr_auc=champ_metrics["pr_auc"],
            gini=champ_metrics["gini"],
            ks_statistic=champ_metrics["ks_statistic"],
            brier_score=champ_metrics["brier_score"],
            is_active=True,
        ))
        db.commit()

        df = build_training_frame(customers, history)
        proba = model.predict_proba(df[ALL_FEATURES])[:, 1]
        predictions = []
        for i, row in df.iterrows():
            pd_value = float(proba[i])
            decision_info = evaluate_application(pd_value, row["total_debt"], row["income"])
            predictions.append(RiskPrediction(
                customer_id=int(row["customer_id"]),
                model_version="v1.0.0",
                probability_of_default=round(pd_value, 6),
                risk_score=pd_to_score(pd_value),
                risk_level=risk_level(pd_value),
                decision=decision_info["decision"],
                suggested_interest_rate=decision_info["suggested_interest_rate"],
                approved_amount=decision_info["approved_amount"],
                top_risk_drivers={},
            ))
        db.bulk_save_objects(predictions)
        db.commit()
        print(f"Seeded {len(predictions)} risk_predictions")

        scan_ids = customers["customer_id"].sample(
            n=min(limit_alerts_scan, len(customers)), random_state=7
        ).tolist()
        detected = scan_for_alerts(customers, history, scan_ids, model=model)
        alerts = [
            RiskAlert(
                customer_id=a["customer_id"],
                previous_risk_level=a["previous_risk_level"],
                current_risk_level=a["current_risk_level"],
                previous_pd=a["previous_pd"],
                current_pd=a["current_pd"],
                signals=a["signals"],
                recommended_action=a["recommended_action"],
            )
            for a in detected
        ]
        db.bulk_save_objects(alerts)
        db.commit()
        print(f"Seeded {len(alerts)} risk_alerts (scanned {len(scan_ids)} customers)")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
