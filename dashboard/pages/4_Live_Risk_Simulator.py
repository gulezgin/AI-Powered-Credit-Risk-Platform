import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api_client import post_predict_risk
from theme import page_header, risk_badge

st.set_page_config(page_title="Live Risk Simulator", page_icon="🧮", layout="wide")
page_header("🧮 Live Risk Simulator",
            "Simulate a brand-new loan application through POST /predict-risk — no existing customer required.")

with st.form("application_form"):
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Age", 18, 90, 34)
    occupation = c1.selectbox("Occupation", [
        "Engineer", "Teacher", "Civil Servant", "Business Owner", "Healthcare Worker",
        "Retail Worker", "Driver", "Accountant", "IT Specialist", "Retired",
    ])
    income = c1.number_input("Monthly Income (TL)", 8000, 500000, 85000, step=1000)

    employment_years = c2.number_input("Employment Years", 0.0, 50.0, 3.0)
    credit_history_years = c2.number_input("Credit History Years", 0.0, 50.0, 6.0)
    num_existing_loans = c2.number_input("Existing Loans", 0, 10, 2)
    num_credit_inquiries_6m = c2.number_input("Credit Inquiries (6m)", 0, 15, 3)

    total_debt = c3.number_input("Total Debt (TL)", 0, 5_000_000, 310000, step=1000)
    monthly_payment = c3.number_input("Monthly Payment (TL)", 0, 200000, 9800, step=100)
    credit_utilization = c3.slider("Credit Utilization", 0.0, 1.0, 0.72)
    num_late_payments = c3.number_input("Late Payments", 0, 24, 2)

    c4, c5, c6 = st.columns(3)
    account_balance = c4.number_input("Account Balance (TL)", 0, 2_000_000, 42000, step=500)
    transaction_intensity = c5.number_input("Transaction Intensity (monthly count)", 0, 300, 35)
    loan_amount = c6.number_input("Requested Loan Amount (TL)", 1000, 5_000_000, 250000, step=1000)

    submitted = st.form_submit_button("Run Risk Assessment", type="primary")

if submitted:
    payload = {
        "age": age, "occupation": occupation, "income": income,
        "employment_years": employment_years, "credit_history_years": credit_history_years,
        "num_existing_loans": num_existing_loans, "num_credit_inquiries_6m": num_credit_inquiries_6m,
        "total_debt": total_debt, "monthly_payment": monthly_payment,
        "credit_utilization": credit_utilization, "num_late_payments": num_late_payments,
        "account_balance": account_balance, "transaction_intensity": transaction_intensity,
        "loan_amount": loan_amount,
    }
    try:
        result = post_predict_risk(payload)
    except Exception as e:
        st.error(f"Prediction failed: {e}")
        st.stop()

    st.divider()
    level = result["risk_level"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Credit Risk Score", result["risk_score"])
    c2.metric("Probability of Default", f"{result['probability_of_default'] * 100:.1f}%")
    c3.markdown("**Risk Level**")
    c3.markdown(risk_badge(level), unsafe_allow_html=True)
    c4.metric("Decision", result["decision"])

    if result["decision"] != "REJECT":
        st.success(
            f"✓ {result['decision']} — Loan Amount: {result['approved_amount']:,.0f} TL · "
            f"Suggested Interest Rate: {result['suggested_interest_rate'] * 100:.2f}%"
        )
    else:
        st.error("✗ REJECT — probability of default exceeds policy threshold.")

    if result.get("reason_codes"):
        st.markdown("**Adverse Action Reason Codes** (ECOA / Reg B style)")
        for reason in result["reason_codes"]:
            st.markdown(f"- {reason}")

    st.subheader("Key Risk Drivers (SHAP)")
    drivers = result["key_risk_drivers"]
    if drivers:
        df = pd.DataFrame(drivers).sort_values("contribution")
        colors = ["#C62828" if v > 0 else "#2E7D32" for v in df["contribution"]]
        fig = go.Figure(go.Bar(x=df["contribution"], y=df["feature"], orientation="h", marker_color=colors))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                           xaxis_title="Contribution to PD (higher = more risk)",
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
