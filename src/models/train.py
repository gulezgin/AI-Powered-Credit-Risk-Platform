"""Train & compare Logistic Regression, Random Forest and XGBoost credit-risk
models, calibrate the winner, and persist all artifacts the API/dashboard need.

The training core is dataset-agnostic: it takes a feature spec and a labeled
frame, so the same pipeline runs over the synthetic portfolio and over the real
UCI Taiwanese credit-card dataset (`--dataset uci`) without special-casing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.config import ARTIFACTS_DIR, DATA_RAW_DIR, RANDOM_SEED
from src.features.engineering import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    build_training_frame,
)
from src.models.evaluate import evaluate_model


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    transformers = [("num", StandardScaler(), numeric_features)]
    if categorical_features:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features))
    return ColumnTransformer(transformers=transformers)


def get_candidate_models() -> dict:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=20,
            class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=350, max_depth=4, learning_rate=0.05,
            subsample=0.85, colsample_bytree=0.85, eval_metric="logloss",
            random_state=RANDOM_SEED, n_jobs=-1,
        ),
    }


def train_and_persist(
    df: pd.DataFrame,
    *,
    numeric_features: list[str],
    categorical_features: list[str],
    target: str,
    out_dir: Path,
    dataset_name: str,
    decision_threshold: float = 0.12,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    all_features = numeric_features + categorical_features

    X = df[all_features]
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )

    preprocessor = build_preprocessor(numeric_features, categorical_features)
    results: dict[str, dict] = {}
    fitted_pipelines: dict[str, Pipeline] = {}

    for name, model in get_candidate_models().items():
        pipe = Pipeline([("preprocess", preprocessor), ("model", model)])
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:, 1]
        metrics = evaluate_model(y_test.values, proba, threshold=decision_threshold)
        results[name] = metrics
        fitted_pipelines[name] = pipe
        print(f"{name}: ROC-AUC={metrics['roc_auc']:.4f} PR-AUC={metrics['pr_auc']:.4f} "
              f"KS={metrics['ks_statistic']:.4f} Gini={metrics['gini']:.4f} "
              f"Brier={metrics['brier_score']:.4f}")

    best_name = max(results, key=lambda k: results[k]["roc_auc"])
    print(f"\nBest base model: {best_name}")

    best_pipe = fitted_pipelines[best_name]
    calibrated = CalibratedClassifierCV(best_pipe, method="isotonic", cv=5)
    calibrated.fit(X_train, y_train)
    calibrated_proba = calibrated.predict_proba(X_test)[:, 1]
    calibrated_metrics = evaluate_model(y_test.values, calibrated_proba, threshold=decision_threshold)
    results[f"{best_name}_calibrated"] = calibrated_metrics
    print(f"{best_name}_calibrated: ROC-AUC={calibrated_metrics['roc_auc']:.4f} "
          f"Brier={calibrated_metrics['brier_score']:.4f} (vs uncalibrated "
          f"{results[best_name]['brier_score']:.4f})")

    joblib.dump(calibrated, out_dir / "credit_risk_model.joblib")
    joblib.dump(best_pipe, out_dir / "best_uncalibrated_pipeline.joblib")

    payload = {
        "dataset": dataset_name,
        "champion_model": best_name,
        "comparison": results,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "base_default_rate": float(y.mean()),
    }
    with open(out_dir / "model_metrics.json", "w") as f:
        json.dump(payload, f, indent=2)

    with open(out_dir / "feature_list.json", "w") as f:
        json.dump({
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "all_features": all_features,
            "target": target,
        }, f, indent=2)

    reference = {}
    for col in numeric_features:
        reference[col] = {
            "mean": float(X_train[col].mean()),
            "std": float(X_train[col].std()),
            # Equal-probability decile edges, so PSI's "expected" distribution is
            # uniform by construction — unequal quantile spacing would make even
            # a zero-drift population look artificially skewed against a naive
            # uniform baseline.
            "quantiles": np.quantile(X_train[col], np.linspace(0, 1, 11)).tolist(),
        }
    with open(out_dir / "reference_distribution.json", "w") as f:
        json.dump(reference, f, indent=2)

    # Small labeled sample for SHAP background + dashboard demo customers
    sample = df.sample(n=min(2000, len(df)), random_state=RANDOM_SEED)
    sample.to_csv(out_dir / "model_input_sample.csv", index=False)

    print(f"\nSaved calibrated model -> {out_dir / 'credit_risk_model.joblib'}")
    print(f"Saved metrics -> {out_dir / 'model_metrics.json'}")
    return payload


def train_synthetic() -> dict:
    customers = pd.read_csv(DATA_RAW_DIR / "customers.csv")
    history = pd.read_csv(DATA_RAW_DIR / "credit_history.csv")
    df = build_training_frame(customers, history)
    return train_and_persist(
        df,
        numeric_features=NUMERIC_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
        target=TARGET,
        out_dir=ARTIFACTS_DIR,
        dataset_name="synthetic",
    )


def train_uci() -> dict:
    from src.datasets import uci_credit

    customers, _ = uci_credit.load()
    return train_and_persist(
        customers,
        numeric_features=uci_credit.NUMERIC_FEATURES,
        categorical_features=uci_credit.CATEGORICAL_FEATURES,
        target=uci_credit.TARGET,
        out_dir=ARTIFACTS_DIR / "uci",
        dataset_name="uci_credit_default",
        # Real base default rate is ~22%, so the review threshold sits higher
        # than the synthetic portfolio's ~7%.
        decision_threshold=0.30,
    )


def main():
    parser = argparse.ArgumentParser(description="Train the credit risk model.")
    parser.add_argument("--dataset", choices=["synthetic", "uci"], default="synthetic")
    args = parser.parse_args()

    if args.dataset == "uci":
        train_uci()
    else:
        train_synthetic()


if __name__ == "__main__":
    main()
