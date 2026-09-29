import streamlit as st

GOLD = "#C9A227"
NAVY_DEEP = "#0A0F1E"
NAVY_CARD = "#111A30"
RISK_COLORS = {"LOW": "#2E8B57", "MEDIUM": "#D9A441", "HIGH": "#D9752E", "CRITICAL": "#C0392B"}
RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

_CSS = f"""
<style>
[data-testid="stMetric"] {{
    background: linear-gradient(180deg, {NAVY_CARD} 0%, #0D1526 100%);
    border: 1px solid rgba(201, 162, 39, 0.25);
    border-radius: 10px;
    padding: 14px 16px 10px 16px;
}}
[data-testid="stMetricLabel"] {{
    color: #9AA4B2 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
[data-testid="stMetricValue"] {{
    color: #F2F4F7 !important;
}}
div[data-testid="stExpander"] {{
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
}}
.bankai-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    border: 1px solid rgba(201, 162, 39, 0.4);
    color: {GOLD};
    background: rgba(201, 162, 39, 0.08);
}}
.bankai-header {{
    display: flex;
    align-items: baseline;
    gap: 10px;
    border-bottom: 2px solid rgba(201, 162, 39, 0.35);
    padding-bottom: 10px;
    margin-bottom: 4px;
}}
.bankai-header h1 {{
    margin: 0;
    font-size: 1.9rem;
}}
.bankai-sub {{
    color: #8a93a3;
    font-size: 0.85rem;
    margin-top: 2px;
}}
section[data-testid="stSidebar"] {{
    border-right: 1px solid rgba(201, 162, 39, 0.15);
}}
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str, badge: str = "RISK PLATFORM"):
    inject()
    st.markdown(
        f"""
        <div class="bankai-header">
          <h1>{title}</h1>
          <span class="bankai-badge">{badge}</span>
        </div>
        <div class="bankai-sub">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(level: str) -> str:
    color = RISK_COLORS.get(level, "#888")
    return (
        f'<span style="background:{color}22;color:{color};border:1px solid {color}66;'
        f'padding:3px 12px;border-radius:999px;font-weight:700;letter-spacing:.03em;">{level}</span>'
    )
