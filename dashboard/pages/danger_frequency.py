"""Dashboard 2: Frequency of dangerous AQI days (Poor / Very Poor / Severe) across cities."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.filters import render_filter_state
from dashboard.config import DANGEROUS_AQI_BUCKETS
from dashboard.data.schema import COL_AQI_BUCKET, COL_CITY, COL_DATE
from dashboard.data.transform import apply_filters, dangerous_day_counts_by_city
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day

# Colours per dangerous bucket
_BUCKET_COLORS = {
    "Poor": "#F39C12",       # amber
    "Very Poor": "#E74C3C",  # red
    "Severe": "#8E44AD",     # deep purple
}


def _stacked_bar_by_city(df: pd.DataFrame) -> go.Figure:
    """Stacked bar: each city has three bars (Poor / Very Poor / Severe)."""
    sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(text="No dangerous-day data", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return fig

    counts = (
        sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
        .size()
        .rename(columns={"size": "days"})
    )

    # Enforce bucket order for consistent stacking
    bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in counts[COL_AQI_BUCKET].unique()]
    counts[COL_AQI_BUCKET] = pd.Categorical(counts[COL_AQI_BUCKET], categories=bucket_order, ordered=True)
    counts = counts.sort_values([COL_AQI_BUCKET, "days"], ascending=[True, False])

    # Order cities by total dangerous days (most first)
    city_totals = counts.groupby(COL_CITY)["days"].sum().sort_values(ascending=False)
    city_order = city_totals.index.tolist()

    fig = px.bar(
        counts,
        x=COL_CITY,
        y="days",
        color=COL_AQI_BUCKET,
        color_discrete_map=_BUCKET_COLORS,
        category_orders={COL_CITY: city_order, COL_AQI_BUCKET: bucket_order},
        barmode="stack",
        text="days",
    )
    fig.update_traces(textposition="inside", texttemplate="%{text}")
    fig.update_layout(
        title="Dangerous AQI Days by City (Stacked: Poor / Very Poor / Severe)",
        xaxis_title="",
        yaxis_title="Number of Days",
        height=520,
        legend_title_text="AQI Bucket",
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def _grouped_bar_by_city(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Grouped bar: side-by-side comparison of each bucket per city (top N)."""
    sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
    if sub.empty:
        return go.Figure()

    counts = (
        sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
        .size()
        .rename(columns={"size": "days"})
    )
    city_totals = counts.groupby(COL_CITY)["days"].sum().sort_values(ascending=False)
    top_cities = city_totals.head(top_n).index.tolist()
    counts = counts[counts[COL_CITY].isin(top_cities)]

    bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in counts[COL_AQI_BUCKET].unique()]

    fig = px.bar(
        counts,
        x=COL_CITY,
        y="days",
        color=COL_AQI_BUCKET,
        color_discrete_map=_BUCKET_COLORS,
        barmode="group",
        category_orders={COL_CITY: top_cities, COL_AQI_BUCKET: bucket_order},
    )
    fig.update_layout(
        title=f"Top {top_n} Cities — Dangerous Days by Bucket (Grouped)",
        xaxis_title="",
        yaxis_title="Number of Days",
        height=500,
        legend_title_text="AQI Bucket",
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def _percentage_bar(df: pd.DataFrame) -> go.Figure:
    """100 % stacked bar showing proportion of each dangerous bucket per city."""
    sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
    if sub.empty:
        return go.Figure()

    counts = (
        sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
        .size()
        .rename(columns={"size": "days"})
    )
    totals = counts.groupby(COL_CITY)["days"].transform("sum")
    counts["pct"] = (counts["days"] / totals * 100).round(1)

    city_order = (
        counts.groupby(COL_CITY)["days"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in counts[COL_AQI_BUCKET].unique()]

    fig = px.bar(
        counts,
        y=COL_CITY,
        x="pct",
        color=COL_AQI_BUCKET,
        orientation="h",
        color_discrete_map=_BUCKET_COLORS,
        category_orders={COL_CITY: list(reversed(city_order)), COL_AQI_BUCKET: bucket_order},
        text="pct",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
    fig.update_layout(
        title="Proportion of Dangerous Buckets within Each City (%)",
        xaxis_title="Percentage of Dangerous Days",
        yaxis_title="",
        height=max(420, len(city_order) * 28),
        legend_title_text="AQI Bucket",
        barmode="stack",
    )
    return fig


def _yearly_trend(df: pd.DataFrame) -> go.Figure:
    """Line chart — total dangerous days per year across all cities."""
    sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
    if sub.empty or COL_DATE not in sub.columns:
        return go.Figure()

    sub[COL_DATE] = pd.to_datetime(sub[COL_DATE], errors="coerce")
    sub = sub.dropna(subset=[COL_DATE])
    sub["year"] = sub[COL_DATE].dt.year

    yearly = (
        sub.groupby(["year", COL_AQI_BUCKET], as_index=False)
        .size()
        .rename(columns={"size": "days"})
    )
    bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in yearly[COL_AQI_BUCKET].unique()]

    fig = px.line(
        yearly,
        x="year",
        y="days",
        color=COL_AQI_BUCKET,
        markers=True,
        color_discrete_map=_BUCKET_COLORS,
        category_orders={COL_AQI_BUCKET: bucket_order},
    )
    fig.update_layout(
        title="Dangerous Days Over Time (All Cities Combined)",
        xaxis_title="Year",
        yaxis_title="Number of Days",
        height=420,
        legend_title_text="AQI Bucket",
    )
    return fig


def _heatmap_city_bucket(df: pd.DataFrame) -> go.Figure:
    """Heatmap: cities × dangerous buckets (count of days)."""
    sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
    if sub.empty:
        return go.Figure()

    counts = (
        sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
        .size()
        .rename(columns={"size": "days"})
    )
    pivot = counts.pivot_table(values="days", index=COL_CITY, columns=COL_AQI_BUCKET, fill_value=0)
    # Order columns
    for b in ("Severe", "Very Poor", "Poor"):
        if b not in pivot.columns:
            pivot[b] = 0
    pivot = pivot[["Poor", "Very Poor", "Severe"]]
    pivot["_total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("_total", ascending=True).drop(columns="_total")

    fig = px.imshow(
        pivot,
        text_auto=True,
        color_continuous_scale="OrRd",
        aspect="auto",
    )
    fig.update_layout(
        title="Dangerous Days Heatmap (City × Bucket)",
        xaxis_title="AQI Bucket",
        yaxis_title="",
        height=max(420, len(pivot) * 28),
        coloraxis_colorbar_title="Days",
    )
    return fig


# ── Page entry ───────────────────────────────────────────────────────────────
def render() -> None:
    page_header(
        "⚠️ Dangerous Pollution Frequency",
        "How are dangerous AQI days (Poor, Very Poor, Severe) "
        "distributed across cities?",
    )

    raw = get_city_day()
    filters = render_filter_state(
        raw, key_prefix="df_", show_pollutants=False, show_buckets=False,
    )
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    if df.empty:
        st.warning("No data available. Ensure `city_day.csv` is loaded.")
        return

    # --- KPIs ---------------------------------------------------------------
    section("Key Figures")
    danger = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)]
    total_records = len(df[df[COL_AQI_BUCKET].notna()])
    danger_count = len(danger)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records (with label)", f"{total_records:,}")
    col2.metric("⚠️ Dangerous Days Total", f"{danger_count:,}")
    col3.metric(
        "Dangerous %",
        f"{danger_count / total_records * 100:.1f}%" if total_records else "—",
    )
    # City with most dangerous days
    ddc = dangerous_day_counts_by_city(df)
    if not ddc.empty:
        col4.metric("🏭 Worst City", ddc.iloc[0][COL_CITY])
    else:
        col4.metric("🏭 Worst City", "—")

    # --- Stacked bar --------------------------------------------------------
    section("Stacked Bar — All Cities")
    show_chart(_stacked_bar_by_city(df))

    # --- Grouped bar (top N) ------------------------------------------------
    section("Grouped Comparison (Top N)")
    top_n = st.slider(
        "Number of cities to show",
        min_value=5,
        max_value=min(26, df[COL_CITY].nunique()),
        value=min(15, df[COL_CITY].nunique()),
        key="df_top_n",
    )
    show_chart(_grouped_bar_by_city(df, top_n))

    # --- Percentage bar -----------------------------------------------------
    section("Proportion Breakdown (%)")
    st.caption(
        "Among dangerous days only — what proportion falls into "
        "Poor vs Very Poor vs Severe for each city?"
    )
    show_chart(_percentage_bar(df))

    # --- Heatmap ------------------------------------------------------------
    section("Heatmap (City × Bucket)")
    show_chart(_heatmap_city_bucket(df))

    # --- Yearly trend -------------------------------------------------------
    section("Yearly Trend of Dangerous Days")
    show_chart(_yearly_trend(df))

    # --- Raw table ----------------------------------------------------------
    section("Data Table")
    with st.expander("Show dangerous day counts by city"):
        st.dataframe(
            ddc.rename(columns={"danger_days": "Dangerous Days"}).reset_index(drop=True),
            use_container_width=True,
        )
