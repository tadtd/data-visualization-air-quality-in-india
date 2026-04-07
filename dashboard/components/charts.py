"""Plotly chart factories (placeholders / simple views)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.config import CHART_COLOR_SEQUENCE, DANGEROUS_AQI_BUCKETS


def line_placeholder(title: str = "Trend") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text="Chart placeholder — connect data in transforms",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
    )
    fig.update_layout(title=title, height=360, margin=dict(t=40, b=40))
    return fig


def monthly_aqi_line(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return line_placeholder("Monthly mean AQI")
    fig = px.line(
        df,
        x="year_month",
        y="aqi_mean",
        markers=True,
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
    )
    fig.update_layout(
        title="Monthly mean AQI",
        xaxis_title="Month",
        yaxis_title="Mean AQI",
        height=400,
    )
    return fig


def city_bar_top_bottom(df: pd.DataFrame, *, top_n: int = 10) -> go.Figure:
    if df.empty:
        return line_placeholder("City mean AQI")
    top = df.head(top_n)
    bottom = df.tail(top_n).sort_values("aqi_mean", ascending=True)
    sub = pd.concat([top, bottom], ignore_index=True)
    sub["_group"] = ["Top"] * len(top) + ["Bottom"] * len(bottom)
    fig = px.bar(
        sub,
        x="City",
        y="aqi_mean",
        color="_group",
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
    )
    fig.update_layout(
        title=f"Top / bottom {top_n} cities by mean AQI",
        xaxis_title="City",
        yaxis_title="Mean AQI",
        height=450,
        showlegend=True,
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def dangerous_days_bar(df: pd.DataFrame, *, top_n: int = 15) -> go.Figure:
    if df.empty:
        return line_placeholder("Dangerous-day counts")
    sub = df.head(top_n)
    fig = px.bar(
        sub,
        x="City",
        y="danger_days",
        color_discrete_sequence=[CHART_COLOR_SEQUENCE[0]],
    )
    fig.update_layout(
        title=f"Days in {', '.join(sorted(DANGEROUS_AQI_BUCKETS))} (top {top_n})",
        xaxis_title="City",
        yaxis_title="Day count",
        height=450,
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def correlation_heatmap(df: pd.DataFrame, cols: list[str]) -> go.Figure:
    """Pearson correlation heatmap for numeric columns present in df."""
    use = [c for c in cols if c in df.columns]
    if len(use) < 2:
        return line_placeholder("Correlation heatmap")
    num = df[use].apply(pd.to_numeric, errors="coerce")
    corr = num.corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(title="Pollutant / AQI correlation (Pearson)", height=520)
    return fig


def show_chart(fig: go.Figure, *, use_container_width: bool = True) -> None:
    st.plotly_chart(fig, use_container_width=use_container_width)
