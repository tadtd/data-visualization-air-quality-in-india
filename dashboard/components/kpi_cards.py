"""KPI row using native st.metric (theme-safe; no custom HTML/CSS)."""

from __future__ import annotations

import math

import streamlit as st


def _format(v: float | int | str) -> str:
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return "—"
        return f"{v:,.1f}" if v != int(v) else f"{int(v):,}"
    return str(v)


def render_kpi_row(
    metrics: dict[str, float | int | str],
    *,
    columns: int = 4,
    subtitles: dict[str, str] | None = None,
) -> None:
    """Display metrics in a row; optional subtitles render as captions below each metric."""
    subs = subtitles or {}
    keys = list(metrics.keys())
    cols = st.columns(min(columns, len(keys)) or 1)
    for i, k in enumerate(keys):
        with cols[i % len(cols)]:
            v = metrics[k]
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                display = "—"
            else:
                display = _format(v) if isinstance(v, float) else v
            st.metric(k, display)
            sub = subs.get(k, "")
            if sub:
                st.caption(sub)
