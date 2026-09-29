import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api_client import get_customer, get_customer_history, post_credit_decision
from theme import page_header, risk_badge

st.set_page_config(page_title="Customer 360", page_icon="🔎", layout="wide")
page_header("🔎 Customer 360", "Full underwriting view for an existing customer: score, decision, SHAP drivers, behavioral trend.")

customer_id = st.number_input("Customer ID", min_value=10001, value=10001, step=1)

if st.button("Load Customer", type="primary"):
    try:
        customer = get_customer(int(customer_id))
        history = get_customer_history(int(customer_id))
        decision = post_credit_decision(int(customer_id), customer["total_debt"])
    except Exception as e:
        st.error(f"Could not load customer {customer_id}: {e}")
        st.stop()

    risk_level = decision["risk_level"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Credit Risk Score", decision["risk_score"])
    c2.metric("Probability of Default", f"{decision['probability_of_default'] * 100:.1f}%")
    c3.markdown("**Risk Level**")
    c3.markdown(risk_badge(risk_level), unsafe_allow_html=True)
    c4.metric("Decision", decision["decision"])

    if decision.get("reason_codes"):
        st.markdown("**Adverse Action Reason Codes** (ECOA / Reg B style)")
        for reason in decision["reason_codes"]:
            st.markdown(f"- {reason}")

    st.divider()
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Profile")
        st.write(f"**Occupation:** {customer['occupation']}")
        st.write(f"**Age:** {customer['age']}")
        st.write(f"**Monthly Income:** {customer['income']:,.0f} TL")
        st.write(f"**Total Debt:** {customer['total_debt']:,.0f} TL")
        st.write(f"**Credit Utilization:** {customer['credit_utilization'] * 100:.0f}%")
        st.write(f"**Account Balance:** {customer['account_balance']:,.0f} TL")
        st.write(f"**Employment:** {customer['employment_years']} years")
        if decision["suggested_interest_rate"]:
            st.write(f"**Suggested Interest Rate:** {decision['suggested_interest_rate'] * 100:.2f}%")
        st.write(f"**Approved Amount:** {decision['approved_amount']:,.0f} TL")

    with right:
        st.subheader("SHAP Explanation — Key Risk Drivers")
        drivers = decision["key_risk_drivers"]
        if drivers:
            df = pd.DataFrame(drivers).sort_values("contribution")
            colors = ["#C62828" if v > 0 else "#2E7D32" for v in df["contribution"]]
            fig = go.Figure(go.Bar(
                x=df["contribution"], y=df["feature"], orientation="h", marker_color=colors,
            ))
            fig.update_layout(
                height=320, margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Contribution to PD (higher = more risk)",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No SHAP drivers available.")

    st.divider()
    st.subheader("12-Month Behavioral Trend")
    hist_df = pd.DataFrame(history)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=hist_df["month_index"], y=hist_df["credit_utilization"] * 100,
        name="Credit Utilization (%)", yaxis="y1", line=dict(color="#EF6C00"),
    ))
    fig2.add_trace(go.Scatter(
        x=hist_df["month_index"], y=hist_df["account_balance"],
        name="Account Balance (TL)", yaxis="y2", line=dict(color="#1565C0"),
    ))
    fig2.update_layout(
        height=350, margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Month",
        yaxis=dict(title="Credit Utilization (%)"),
        yaxis2=dict(title="Account Balance (TL)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)
