import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _get(path: str, params: dict | None = None):
    resp = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, json: dict):
    resp = requests.post(f"{API_BASE_URL}{path}", json=json, timeout=30)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=30)
def get_portfolio_summary():
    return _get("/portfolio/summary")


@st.cache_data(ttl=30)
def get_alerts(risk_level: str | None = None, resolved: bool | None = None, limit: int = 100):
    params = {"limit": limit}
    if risk_level:
        params["risk_level"] = risk_level
    if resolved is not None:
        params["resolved"] = resolved
    return _get("/alerts", params=params)


@st.cache_data(ttl=30)
def get_customer(customer_id: int):
    return _get(f"/customer/{customer_id}")


@st.cache_data(ttl=30)
def get_customer_history(customer_id: int):
    return _get(f"/customer/{customer_id}/risk-history")


def post_credit_decision(customer_id: int, requested_amount: float):
    return _post("/credit-decision", {"customer_id": customer_id, "requested_amount": requested_amount})


def post_predict_risk(payload: dict):
    return _post("/predict-risk", payload)


@st.cache_data(ttl=60)
def get_model_metrics():
    return _get("/model/metrics")


@st.cache_data(ttl=60)
def get_model_monitoring():
    return _get("/model/monitoring")


@st.cache_data(ttl=60)
def get_expected_loss():
    return _get("/portfolio/expected-loss")


@st.cache_data(ttl=60)
def get_fairness():
    return _get("/portfolio/fairness")


def post_stress_test(unemployment_shock_pp: float, rate_shock_pp: float, sample_size: int = 5000):
    return _post("/portfolio/stress-test", {
        "unemployment_shock_pp": unemployment_shock_pp,
        "rate_shock_pp": rate_shock_pp,
        "sample_size": sample_size,
    })
