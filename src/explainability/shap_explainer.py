"""Per-customer SHAP explanations for the credit-risk model.

Explains the *calibrated* pipeline (not a pre-calibration model) so the
reported top-driver contributions live in the same probability space as the
`probability_of_default` shown to the user — explaining the uncalibrated,
class-weight-shifted model instead would attribute risk on a completely
different probability scale that doesn't match what's actually reported.

SHAP's tabular permutation masker requires an all-numeric matrix (it calls
`np.isclose` internally), so the categorical `occupation` feature is
one-hot encoded for the masker and decoded back to a string column just
before calling the calibrated pipeline, which expects raw features.
"""
from __future__ import annotations

from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import shap

from src.config import ARTIFACTS_DIR, MODEL_PATH, RANDOM_SEED
from src.features.engineering import ALL_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES


def _occupation_columns(categories: list[str]) -> list[str]:
    return [f"occupation__{c}" for c in categories]


def _encode(raw: pd.DataFrame, categories: list[str]) -> pd.DataFrame:
    occ_cols = _occupation_columns(categories)
    dummies = pd.get_dummies(raw["occupation"], prefix="occupation", prefix_sep="__")
    dummies = dummies.reindex(columns=occ_cols, fill_value=0)
    return pd.concat([raw[NUMERIC_FEATURES].reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)


def _decode(encoded: np.ndarray, columns: list[str], categories: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(encoded, columns=columns)
    occ_cols = _occupation_columns(categories)
    occ_idx = df[occ_cols].to_numpy(dtype=float).argmax(axis=1)
    df["occupation"] = [categories[i] for i in occ_idx]
    return df[ALL_FEATURES]


@lru_cache(maxsize=1)
def _load_components():
    model = joblib.load(MODEL_PATH)  # calibrated pipeline: preprocess + model + isotonic

    sample = pd.read_csv(ARTIFACTS_DIR / "model_input_sample.csv")
    categories = sorted(sample["occupation"].unique().tolist())
    background_raw = sample[ALL_FEATURES].sample(n=min(60, len(sample)), random_state=RANDOM_SEED)
    background_encoded = _encode(background_raw, categories)
    encoded_columns = list(background_encoded.columns)

    def predict_fn(X_encoded: np.ndarray) -> np.ndarray:
        raw_df = _decode(np.asarray(X_encoded), encoded_columns, categories)
        return model.predict_proba(raw_df)[:, 1]

    explainer = shap.Explainer(
        predict_fn,
        background_encoded.to_numpy(dtype=float),
        feature_names=encoded_columns,
        algorithm="permutation",
        max_evals=4 * len(encoded_columns) + 1,
    )
    return explainer, encoded_columns, categories


def explain_customer(row: pd.DataFrame, top_k: int = 5) -> dict:
    """row: single-row DataFrame with ALL_FEATURES columns (raw, unencoded)."""
    explainer, encoded_columns, categories = _load_components()

    encoded_row = _encode(row[ALL_FEATURES], categories).to_numpy(dtype=float)
    explanation = explainer(encoded_row)
    shap_values = explanation.values[0]
    base_value = float(np.ravel(explanation.base_values)[0])

    contributions: dict[str, float] = {}
    for fname, val in zip(encoded_columns, shap_values):
        original = "occupation" if fname.startswith("occupation__") else fname
        contributions[original] = contributions.get(original, 0.0) + float(val)

    ranked = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)
    # Feature codes, not display labels: the dashboard is bilingual, so the
    # wording belongs where the reader's locale is known.
    top_contributors = [
        {"code": f, "contribution": round(v, 4)} for f, v in ranked[:top_k]
    ]
    return {
        "base_value": round(base_value, 4),
        "predicted_value": round(base_value + sum(contributions.values()), 4),
        "top_contributors": top_contributors,
        "all_contributions": {f: round(v, 4) for f, v in ranked},
    }
