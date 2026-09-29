import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api_client import API_BASE_URL, get_alerts, get_portfolio_summary
from theme import RISK_COLORS, RISK_ORDER, page_header

st.set_page_config(page_title="BankAI Risk Control Center", page_icon="🏦", layout="wide")
page_header("🏦 BankAI — Risk Control Center", f"Connected to API at <code>{API_BASE_URL}</code>")

try:
    summary = get_portfolio_summary()
except Exception as e:
    st.error(f"Could not reach the API at {API_BASE_URL}. Is it running? ({e})")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers", f"{summary['total_customers']:,}")
dist = summary["risk_level_distribution"]
high_risk = dist.get("HIGH", 0) + dist.get("CRITICAL", 0)
col2.metric("High / Critical Risk", f"{high_risk:,}")
col3.metric("Active Alerts", f"{summary['active_alerts']:,}")
col4.metric("Avg Probability of Default", f"{summary['avg_probability_of_default'] * 100:.2f}%")

st.divider()

left, right = st.columns([1, 1.4])

with left:
    st.subheader("Risk Distribution")
    counts = [dist.get(level, 0) for level in RISK_ORDER]
    fig = go.Figure(go.Bar(
        x=counts, y=RISK_ORDER, orientation="h",
        marker_color=[RISK_COLORS[l] for l in RISK_ORDER],
        text=counts, textposition="outside",
    ))
    fig.update_layout(
        height=320, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Customers", yaxis_title=None,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("⚠ Early Warning Alerts")
    try:
        alerts = get_alerts(resolved=False, limit=25)
    except Exception as e:
        alerts = []
        st.warning(f"Could not load alerts: {e}")

    if not alerts:
        st.info("No active early-warning alerts right now.")
    else:
        df = pd.DataFrame(alerts)
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
        df = df[["customer_id", "current_risk_level", "previous_risk_level",
                  "current_pd", "recommended_action", "created_at"]]
        df.columns = ["Customer", "Now", "Was", "Current PD", "Recommended Action", "Detected"]
        st.dataframe(df, use_container_width=True, hide_index=True, height=340)

st.divider()
st.caption(
    "Use the sidebar to open **Customer 360**, **Early Warning Alerts**, "
    "**Model Monitoring**, **Live Risk Simulator** or the **Stress Test Lab**."
)
