import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

for _dir in (DATA_RAW_DIR, DATA_PROCESSED_DIR, ARTIFACTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(ROOT_DIR / 'bankai.db').as_posix()}")

RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
N_CUSTOMERS = int(os.getenv("N_CUSTOMERS", "20000"))
HISTORY_MONTHS = int(os.getenv("HISTORY_MONTHS", "12"))

MODEL_PATH = ARTIFACTS_DIR / "credit_risk_model.joblib"
CALIBRATOR_PATH = ARTIFACTS_DIR / "calibrator.joblib"
PREPROCESSOR_PATH = ARTIFACTS_DIR / "preprocessor.joblib"
SHAP_EXPLAINER_PATH = ARTIFACTS_DIR / "shap_explainer.joblib"
METRICS_PATH = ARTIFACTS_DIR / "model_metrics.json"
FEATURE_LIST_PATH = ARTIFACTS_DIR / "feature_list.json"
MODEL_CARD_PATH = ARTIFACTS_DIR / "model_card.json"
REFERENCE_DISTRIBUTION_PATH = ARTIFACTS_DIR / "reference_distribution.json"

# Business decision thresholds on Probability of Default (PD)
PD_APPROVE_THRESHOLD = float(os.getenv("PD_APPROVE_THRESHOLD", "0.05"))
PD_REVIEW_THRESHOLD = float(os.getenv("PD_REVIEW_THRESHOLD", "0.12"))

# Credit score scaling (FICO-like), higher score = lower risk
SCORE_MIN, SCORE_MAX = 300, 850

EARLY_WARNING_UTILIZATION_JUMP = float(os.getenv("EARLY_WARNING_UTILIZATION_JUMP", "0.20"))
EARLY_WARNING_WITHDRAWAL_JUMP = float(os.getenv("EARLY_WARNING_WITHDRAWAL_JUMP", "0.30"))
