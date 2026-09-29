"""PD -> credit score scorecard transform (points-to-double-odds style)."""
import numpy as np

from src.config import SCORE_MAX, SCORE_MIN

BASE_SCORE = 600
BASE_ODDS = 1.0  # odds of "good" at the base score
PDO = 40  # points to double the odds


def pd_to_score(pd_value: float) -> int:
    pd_value = float(np.clip(pd_value, 1e-6, 1 - 1e-6))
    odds = (1 - pd_value) / pd_value
    factor = PDO / np.log(2)
    offset = BASE_SCORE - factor * np.log(BASE_ODDS)
    score = offset + factor * np.log(odds)
    return int(np.clip(round(score), SCORE_MIN, SCORE_MAX))


def risk_level(pd_value: float) -> str:
    if pd_value < 0.05:
        return "LOW"
    if pd_value < 0.12:
        return "MEDIUM"
    if pd_value < 0.25:
        return "HIGH"
    return "CRITICAL"
