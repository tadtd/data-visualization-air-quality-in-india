"""Shared chart rendering helpers used by page-specific chart classes."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from dashboard.config import get_aqi_threshold_lines


def apply_chart_theme(fig: go.Figure) -> go.Figure:
    """Apply the global dashboard theme to a Plotly figure."""
    fig.update_layout(
        font_family="Be Vietnam Pro",
        title_font_family="Be Vietnam Pro",
    )
    fig.update_xaxes(
        gridcolor="rgba(243,244,246,0.8)",
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color="#9CA3AF", family="Be Vietnam Pro"),
    )
    fig.update_yaxes(
        gridcolor="rgba(243,244,246,0.8)",
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color="#9CA3AF", family="Be Vietnam Pro"),
    )
    return fig


def add_aqi_reference_lines(fig: go.Figure) -> go.Figure:
    """Add horizontal dashed AQI category threshold lines."""
    for line in get_aqi_threshold_lines():
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


def empty_chart(title: str = "Biểu đồ") -> go.Figure:
    """Return a lightweight placeholder when a chart has no data."""
    fig = go.Figure()
    fig.add_annotation(
        text="Không có dữ liệu cho biểu đồ này.",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#9CA3AF", family="Be Vietnam Pro"),
    )
    fig.update_layout(title=title, height=360, margin=dict(t=40, b=40))
    return apply_chart_theme(fig)


def show_chart(fig: go.Figure, *, use_container_width: bool = True) -> None:
    """Render a Plotly figure in Streamlit with the standard width mode."""
    width_mode = "stretch" if use_container_width else "content"
    st.plotly_chart(fig, width=width_mode)
