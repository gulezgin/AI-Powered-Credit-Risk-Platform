"""Model monitoring: Population Stability Index (PSI) per feature against the
training-time reference distribution, plus a simple drift severity label."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.config import REFERENCE_DISTRIBUTION_PATH


def _psi_for_feature(current_values: np.ndarray, reference_quantiles: list[float]) -> float:
    bins = np.unique(reference_quantiles)
    if len(bins) < 3:
        return 0.0
    bins[0], bins[-1] = -np.inf, np.inf

    expected_pct = np.full(len(bins) - 1, 1.0 / (len(bins) - 1))
    actual_counts, _ = np.histogram(current_values, bins=bins)
    actual_pct = actual_counts / max(1, actual_counts.sum())

    expected_pct = np.clip(expected_pct, 1e-4, None)
    actual_pct = np.clip(actual_pct, 1e-4, None)
    psi = float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))
    return round(psi, 4)


def drift_severity(psi: float) -> str:
    if psi < 0.1:
        return "LOW"
    if psi < 0.25:
        return "MEDIUM"
    return "HIGH"


def compute_feature_drift(current_df: pd.DataFrame) -> dict:
    with open(REFERENCE_DISTRIBUTION_PATH) as f:
        reference = json.load(f)

    results = {}
    for feature, stats in reference.items():
        if feature not in current_df.columns:
            continue
        psi = _psi_for_feature(current_df[feature].dropna().values, stats["quantiles"])
        results[feature] = {"psi": psi, "severity": drift_severity(psi)}
    return results


def population_psi(current_df: pd.DataFrame) -> float:
    feature_drift = compute_feature_drift(current_df)
    if not feature_drift:
        return 0.0
    return round(float(np.mean([v["psi"] for v in feature_drift.values()])), 4)
