"""Fair-lending style disparate-impact monitor.

Uses the EEOC/OFCCP "four-fifths (80%) rule" convention: if a group's approval
rate is less than 80% of the reference group's rate, it is flagged for review.
This is a screening heuristic that triggers a compliance investigation — never
a legal conclusion on its own, and never grounds for automated action.

Two details that matter in practice and are easy to get wrong:

1. The reference group must have a meaningful sample. The UGESP guidance notes
   the four-fifths rule is unreliable for small samples, and picking whichever
   tiny segment happens to have the highest approval rate makes every other
   group look adverse. Groups below `min_group_size` are therefore reported but
   excluded from becoming the reference, and are marked `insufficient_sample`
   instead of flagged.
2. A flag does not imply the model used a protected attribute. In this project
   the protected attributes are deliberately excluded from the feature set, so
   any disparity that shows up is a *proxy* effect coming through correlated
   behavioral features — which is precisely what a fair-lending review exists
   to catch.
"""
from __future__ import annotations

import pandas as pd

ADVERSE_IMPACT_THRESHOLD = 0.8
MIN_GROUP_SIZE = 500


def group_disparity(
    df: pd.DataFrame,
    group_col: str = "occupation",
    decision_col: str = "decision",
    pd_col: str = "probability_of_default",
    min_group_size: int = MIN_GROUP_SIZE,
) -> pd.DataFrame:
    grouped = df.groupby(group_col).agg(
        n=(decision_col, "count"),
        avg_pd=(pd_col, "mean"),
        approval_rate=(decision_col, lambda s: (s == "APPROVE").mean()),
    ).reset_index()

    eligible = grouped[grouped["n"] >= min_group_size]
    reference_rate = (
        eligible["approval_rate"].max() if not eligible.empty else grouped["approval_rate"].max()
    )

    grouped["adverse_impact_ratio"] = (
        (grouped["approval_rate"] / reference_rate).round(4) if reference_rate > 0 else 0.0
    )
    grouped["insufficient_sample"] = grouped["n"] < min_group_size
    grouped["flagged"] = (
        (grouped["adverse_impact_ratio"] < ADVERSE_IMPACT_THRESHOLD)
        & ~grouped["insufficient_sample"]
    )
    grouped["avg_pd"] = grouped["avg_pd"].round(4)
    grouped["approval_rate"] = grouped["approval_rate"].round(4)

    return grouped.sort_values("adverse_impact_ratio")
