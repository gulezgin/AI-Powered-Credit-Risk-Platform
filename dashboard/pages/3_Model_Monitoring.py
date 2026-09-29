import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api_client import get_expected_loss, get_fairness, get_model_metrics, get_model_monitoring
from theme import page_header

st.set_page_config(page_title="Model Monitoring", page_icon="📊", layout="wide")
page_header("📊 Model Monitoring", "Performance, calibration, drift, expected loss and fair-lending monitoring.",
            badge="MODEL GOVERNANCE")

try:
    metrics = get_model_metrics()
    monitoring = get_model_monitoring()
    expected_loss = get_expected_loss()
    fairness = get_fairness()
except Exception as e:
    st.error(f"Could not load monitoring data: {e}")
    st.stop()

st.caption(
    f"Champion model: **{metrics['champion_model']}** "
    f"(version `{metrics['model_version']}`, trained {metrics['trained_at']}) "
    f"— {metrics['n_train']:,} train / {metrics['n_test']:,} test rows"
)

champ_key = f"{metrics['champion_model']}_calibrated"
champ = metrics["comparison"][champ_key]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("ROC-AUC", f"{champ['roc_auc']:.3f}")
c2.metric("Gini", f"{champ['gini']:.3f}")
c3.metric("KS Statistic", f"{champ['ks_statistic']:.3f}")
c4.metric("Brier Score", f"{champ['brier_score']:.3f}")
c5.metric("Population PSI", f"{monitoring['population_psi']:.3f}")
c6.metric("Portfolio Expected Loss", f"{expected_loss['total_expected_loss']/1e6:,.1f}M TL",
          help=f"PD × {expected_loss['lgd_assumption']*100:.0f}% LGD × exposure, "
               f"{expected_loss['expected_loss_ratio']*100:.2f}% of {expected_loss['total_exposure']/1e6:,.0f}M TL exposure")

st.divider()
left, right = st.columns([1.3, 1])

with left:
    st.subheader("Model Comparison")
    rows = []
    for name, m in metrics["comparison"].items():
        rows.append({
            "Model": name, "ROC-AUC": m["roc_auc"], "PR-AUC": m["pr_auc"],
            "Gini": m["gini"], "KS": m["ks_statistic"], "Brier": m["brier_score"],
            "Precision": m["precision"], "Recall": m["recall"], "F1": m["f1"],
        })
    df = pd.DataFrame(rows).sort_values("ROC-AUC", ascending=False)
    st.dataframe(df.style.format({c: "{:.3f}" for c in df.columns if c != "Model"}),
                 use_container_width=True, hide_index=True)

    st.subheader("Calibration Curve")
    cal = champ["calibration_curve"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration",
                              line=dict(dash="dash", color="gray")))
    fig.add_trace(go.Scatter(x=cal["mean_predicted"], y=cal["fraction_positive"],
                              mode="lines+markers", name=champ_key, line=dict(color="#1565C0")))
    fig.update_layout(
        height=350, xaxis_title="Mean Predicted PD", yaxis_title="Observed Default Rate",
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Risk Level Distribution")
    dist = monitoring["risk_level_distribution"]
    order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    colors = {"LOW": "#2E7D32", "MEDIUM": "#F9A825", "HIGH": "#EF6C00", "CRITICAL": "#C62828"}
    fig2 = go.Figure(go.Bar(
        x=order, y=[dist.get(k, 0) for k in order],
        marker_color=[colors[k] for k in order],
    ))
    fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10),
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Feature Drift (PSI)")
    drift_rows = [
        {"Feature": f, "PSI": v["psi"], "Severity": v["severity"]}
        for f, v in sorted(monitoring["feature_drift"].items(), key=lambda kv: -kv[1]["psi"])
    ]
    drift_df = pd.DataFrame(drift_rows)

    def _severity_color(val):
        return {"LOW": "background-color: #1b3a1f", "MEDIUM": "background-color: #4a3b0f",
                "HIGH": "background-color: #4a1414"}.get(val, "")

    st.dataframe(
        drift_df.style.map(_severity_color, subset=["Severity"]).format({"PSI": "{:.3f}"}),
        use_container_width=True, hide_index=True, height=300,
    )
    st.caption("PSI < 0.10 stable · 0.10–0.25 moderate shift · > 0.25 significant drift, consider retraining.")

st.divider()
st.subheader("⚖ Fair Lending Monitor")
st.caption(
    "Disparate-impact screen across occupation groups (EEOC four-fifths rule: a group approved "
    "less than 80% as often as the best-approved group is flagged for compliance review). "
    "This dataset has no protected-class attributes — occupation stands in for demonstration only."
)
fair_df = pd.DataFrame(fairness).rename(columns={
    "occupation": "Occupation", "n": "N", "avg_pd": "Avg PD", "approval_rate": "Approval Rate",
    "adverse_impact_ratio": "Adverse Impact Ratio", "flagged": "Flagged",
})


def _flag_color(val):
    return "background-color: #4a1414; color: #ff8a80" if val else ""


st.dataframe(
    fair_df.style.map(_flag_color, subset=["Flagged"])
    .format({"Avg PD": "{:.2%}", "Approval Rate": "{:.2%}", "Adverse Impact Ratio": "{:.3f}"}),
    use_container_width=True, hide_index=True,
)
if fair_df["Flagged"].any():
    st.warning("One or more groups fall below the 80% adverse-impact threshold — flagged for compliance review.")
else:
    st.success("No groups fall below the 80% adverse-impact threshold in the current portfolio.")
