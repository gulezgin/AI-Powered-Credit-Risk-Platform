import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api_client import post_stress_test
from theme import RISK_COLORS, RISK_ORDER, page_header

st.set_page_config(page_title="Stress Test Lab", page_icon="🧪", layout="wide")
page_header(
    "🧪 Stress Test Lab",
    "CCAR/DFAST-style macro scenario: shock the portfolio and re-score it with the same production PD model.",
    badge="RISK MANAGEMENT",
)

with st.expander("How this scenario works", expanded=False):
    st.markdown(
        "- **Unemployment shock** raises revolving credit utilization and lowers income "
        "(households draw on credit lines and lose hours/jobs).\n"
        "- **Rate shock** increases monthly payments on variable-rate debt, raising "
        "debt-to-income and payment-to-income.\n"
        "- The **same calibrated model** used for live decisions re-scores the sampled "
        "portfolio under the shocked assumptions — this isn't a separate stress model.\n"
        "- Expected Loss = PD × 45% LGD × Total Debt (EAD), IFRS 9 / CECL style."
    )

c1, c2, c3 = st.columns(3)
unemployment_shock = c1.slider("Unemployment Shock (+pp)", 0.0, 8.0, 3.0, 0.5)
rate_shock = c2.slider("Interest Rate Shock (+pp)", 0.0, 8.0, 2.0, 0.5)
sample_size = c3.select_slider("Sample Size", options=[1000, 3000, 5000, 10000, 20000], value=5000)

run = st.button("Run Stress Scenario", type="primary")

if run:
    with st.spinner("Re-scoring portfolio under shocked assumptions..."):
        try:
            result = post_stress_test(unemployment_shock, rate_shock, sample_size)
        except Exception as e:
            st.error(f"Stress test failed: {e}")
            st.stop()

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline Avg PD", f"{result['baseline_avg_pd']*100:.2f}%")
    c2.metric("Stressed Avg PD", f"{result['stressed_avg_pd']*100:.2f}%",
              delta=f"+{result['avg_pd_delta_pp']:.2f} pp")
    base_el = result["baseline_expected_loss"]["total_expected_loss"]
    stress_el = result["stressed_expected_loss"]["total_expected_loss"]
    c3.metric("Expected Loss", f"{stress_el:,.0f} TL",
              delta=f"+{stress_el - base_el:,.0f} TL vs baseline")

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Risk Distribution: Baseline vs. Stressed")
        base_dist = result["baseline_risk_distribution"]
        stress_dist = result["stressed_risk_distribution"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Baseline", x=RISK_ORDER,
                              y=[base_dist.get(k, 0) for k in RISK_ORDER],
                              marker_color="#5b6472"))
        fig.add_trace(go.Bar(name="Stressed", x=RISK_ORDER,
                              y=[stress_dist.get(k, 0) for k in RISK_ORDER],
                              marker_color=[RISK_COLORS[k] for k in RISK_ORDER]))
        fig.update_layout(barmode="group", height=380, margin=dict(l=10, r=10, t=10, b=10),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Expected Loss by Risk Level")
        base_el_lvl = result["baseline_expected_loss"]["expected_loss_by_risk_level"]
        stress_el_lvl = result["stressed_expected_loss"]["expected_loss_by_risk_level"]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Baseline", x=RISK_ORDER,
                               y=[base_el_lvl.get(k, 0) for k in RISK_ORDER],
                               marker_color="#5b6472"))
        fig2.add_trace(go.Bar(name="Stressed", x=RISK_ORDER,
                               y=[stress_el_lvl.get(k, 0) for k in RISK_ORDER],
                               marker_color=[RISK_COLORS[k] for k in RISK_ORDER]))
        fig2.update_layout(barmode="group", height=380, margin=dict(l=10, r=10, t=10, b=10),
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        f"Expected loss ratio: {result['baseline_expected_loss']['expected_loss_ratio']*100:.2f}% "
        f"(baseline) → {result['stressed_expected_loss']['expected_loss_ratio']*100:.2f}% (stressed) "
        f"on {result['sample_size']:,} sampled accounts."
    )
