from fastapi import APIRouter

from api.schemas import PredictRiskRequest, PredictRiskResponse
from src.models.inference import score_application

router = APIRouter(tags=["risk"])


@router.post("/predict-risk", response_model=PredictRiskResponse)
def predict_risk(payload: PredictRiskRequest):
    result = score_application(payload.model_dump())
    return result
