"""KPI metric cards."""

from __future__ import annotations

import math

import streamlit as st


def render_kpi_row(metrics: dict[str, float | int | str], *, columns: int = 3) -> None:
    """Display a row of metric columns."""
    keys = list(metrics.keys())
    cols = st.columns(min(columns, len(keys)) or 1)
    for i, k in enumerate(keys):
        v = metrics[k]
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            display = "—"
        else:
            display = v
        cols[i % len(cols)].metric(label=k.replace("_", " ").title(), value=display)
