import pandas as pd
import streamlit as st

from api_client import get_alerts
from theme import page_header

st.set_page_config(page_title="Early Warning Alerts", page_icon="⚠", layout="wide")
page_header("⚠ Early Warning Alerts",
            "Customers whose model-estimated risk bucket has deteriorated between two points in time.")

col1, col2, col3 = st.columns(3)
risk_filter = col1.selectbox("Current Risk Level", ["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
resolved_filter = col2.selectbox("Status", ["Active only", "Resolved only", "All"])
limit = col3.slider("Max results", 10, 500, 100)

resolved = None
if resolved_filter == "Active only":
    resolved = False
elif resolved_filter == "Resolved only":
    resolved = True

try:
    alerts = get_alerts(
        risk_level=None if risk_filter == "All" else risk_filter,
        resolved=resolved,
        limit=limit,
    )
except Exception as e:
    st.error(f"Could not load alerts: {e}")
    st.stop()

if not alerts:
    st.info("No alerts match these filters.")
else:
    st.metric("Matching Alerts", len(alerts))
    for alert in alerts:
        with st.expander(
            f"Customer #{alert['customer_id']} — "
            f"{alert['previous_risk_level']} → {alert['current_risk_level']}  "
            f"(PD {alert['previous_pd']*100:.1f}% → {alert['current_pd']*100:.1f}%)"
        ):
            st.write("**Detected signals:**")
            for s in alert["signals"]:
                st.write(f"• {s}")
            st.write(f"**Recommended action:** {alert['recommended_action']}")
            st.caption(f"Detected at {alert['created_at']} — resolved: {alert['resolved']}")
