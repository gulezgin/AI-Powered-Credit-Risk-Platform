"""Banking-relevant model evaluation metrics beyond plain accuracy."""
from __future__ import annotations

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def ks_statistic(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    return float(np.max(np.abs(tpr - fpr)))


def gini_coefficient(auc: float) -> float:
    return float(2 * auc - 1)


def evaluate_model(y_true: np.ndarray, y_proba: np.ndarray, threshold: float = 0.12) -> dict:
    y_pred = (y_proba >= threshold).astype(int)
    auc = float(roc_auc_score(y_true, y_proba))

    cal_frac_pos, cal_mean_pred = calibration_curve(y_true, y_proba, n_bins=10, strategy="quantile")

    return {
        "roc_auc": auc,
        "pr_auc": float(average_precision_score(y_true, y_proba)),
        "gini": gini_coefficient(auc),
        "ks_statistic": ks_statistic(y_true, y_proba),
        "brier_score": float(brier_score_loss(y_true, y_proba)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "decision_threshold": threshold,
        "default_rate_actual": float(np.mean(y_true)),
        "default_rate_predicted": float(np.mean(y_pred)),
        "calibration_curve": {
            "mean_predicted": cal_mean_pred.tolist(),
            "fraction_positive": cal_frac_pos.tolist(),
        },
    }
