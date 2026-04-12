"""Shared chart rendering helpers used by page-specific chart classes."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from dashboard.config import AQI_THRESHOLD_LINES 


def apply_chart_theme(fig: go.Figure) -> go.Figure:
    """Apply the global dashboard theme to a Plotly figure."""
    fig.update_xaxes(
        gridcolor="rgba(243,244,246,0.8)",
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color="#9CA3AF"),
    )
    fig.update_yaxes(
        gridcolor="rgba(243,244,246,0.8)",
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color="#9CA3AF"),
    )
    return fig


def add_aqi_reference_lines(fig: go.Figure) -> go.Figure:
    """Add horizontal dashed AQI category threshold lines."""
    for line in AQI_THRESHOLD_LINES:
        fig.add_hline(
            y=line["y"],
            line_dash="dash",
            line_color=line["color"],
            line_width=1,
            annotation_text=line["label"],
            annotation_position="right",
            annotation_font_size=10,
            annotation_font_color=line["color"],
        )
    return fig


def empty_chart(title: str = "Trend") -> go.Figure:
    """Return a lightweight placeholder when a chart has no data."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available for this chart.",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#9CA3AF"),
    )
    fig.update_layout(title=title, height=360, margin=dict(t=40, b=40))
    return apply_chart_theme(fig)


def show_chart(fig: go.Figure, *, use_container_width: bool = True) -> None:
    """Render a Plotly figure in Streamlit with the standard width mode."""
    width_mode = "stretch" if use_container_width else "content"
    st.plotly_chart(fig, width=width_mode)
