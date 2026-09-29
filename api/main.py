from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    alerts,
    customers,
    decisions,
    model_metrics,
    predict,
    real_dataset,
    risk_management,
)

app = FastAPI(
    title="BankAI — Credit Risk & Early Warning Intelligence Platform",
    description=(
        "End-to-end banking credit risk decision API: probability-of-default "
        "scoring, explainable AI drivers, a business decision engine and "
        "early-warning alerts on deteriorating customer behavior."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(customers.router)
app.include_router(alerts.router)
app.include_router(decisions.router)
app.include_router(model_metrics.router)
app.include_router(risk_management.router)
app.include_router(real_dataset.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "BankAI Credit Risk Platform"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
