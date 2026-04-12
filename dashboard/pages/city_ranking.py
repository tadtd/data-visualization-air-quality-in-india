"""Dashboard 1: Top most-polluted & cleanest cities by average AQI."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.filters import render_filter_state
from dashboard.config import CHART_COLOR_SEQUENCE
from dashboard.data.schema import COL_AQI, COL_CITY, COL_DATE
from dashboard.data.transform import apply_filters, city_mean_aqi
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day

# ── Colour scales ────────────────────────────────────────────────────────────
_POLLUTED_COLOR = "#E74C3C"   # red-ish for most polluted
_CLEAN_COLOR = "#2ECC71"      # green for cleanest
_GRADIENT_SCALE = "RdYlGn_r"  # red = high AQI, green = low AQI


def _top_bottom_bar(df_rank: pd.DataFrame, top_n: int) -> go.Figure:
    """Horizontal bar chart showing top-N most-polluted (left) vs cleanest (right)."""
    if df_rank.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return fig

    worst = df_rank.head(top_n).copy()
    best = df_rank.tail(top_n).sort_values("aqi_mean", ascending=True).copy()

    worst["group"] = "Most polluted"
    best["group"] = "Cleanest"

    combined = pd.concat([worst, best], ignore_index=True)

    fig = px.bar(
        combined,
        y=COL_CITY,
        x="aqi_mean",
        color="group",
        orientation="h",
        color_discrete_map={
            "Most polluted": _POLLUTED_COLOR,
            "Cleanest": _CLEAN_COLOR,
        },
        text="aqi_mean",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        title=f"Top {top_n} Most Polluted vs Cleanest Cities (Mean AQI)",
        xaxis_title="Mean AQI",
        yaxis_title="",
        height=max(400, top_n * 38),
        legend_title_text="",
        yaxis=dict(categoryorder="total ascending"),
        margin=dict(l=10, r=60),
    )
    return fig


def _full_ranking_bar(df_rank: pd.DataFrame) -> go.Figure:
    """Vertical bar chart of ALL cities coloured by AQI intensity."""
    if df_rank.empty:
        return go.Figure()

    fig = px.bar(
        df_rank,
        x=COL_CITY,
        y="aqi_mean",
        color="aqi_mean",
        color_continuous_scale=_GRADIENT_SCALE,
        text="aqi_mean",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        title="All Cities Ranked by Mean AQI (highest → lowest)",
        xaxis_title="",
        yaxis_title="Mean AQI",
        height=520,
        coloraxis_colorbar_title="AQI",
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def _aqi_box_plot(df: pd.DataFrame, cities: list[str]) -> go.Figure:
    """Box-plot of daily AQI distributions for selected cities."""
    sub = df[df[COL_CITY].isin(cities) & df[COL_AQI].notna()].copy()
    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for selected cities", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return fig

    fig = px.box(
        sub,
        x=COL_CITY,
        y=COL_AQI,
        color=COL_CITY,
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
        points=False,
    )
    fig.update_layout(
        title="Daily AQI Distribution per City",
        xaxis_title="",
        yaxis_title="AQI",
        height=480,
        showlegend=False,
    )
    fig.update_xaxes(tickangle=-35)
    return fig


def _yearly_mean_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap: rows = cities, columns = years, values = mean AQI."""
    if df.empty or COL_DATE not in df.columns:
        return go.Figure()

    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE, COL_AQI])
    t["year"] = t[COL_DATE].dt.year

    pivot = t.pivot_table(values=COL_AQI, index=COL_CITY, columns="year", aggfunc="mean")
    pivot = pivot.sort_values(by=pivot.columns.tolist(), ascending=False)

    fig = px.imshow(
        pivot,
        color_continuous_scale=_GRADIENT_SCALE,
        text_auto=".0f",
        aspect="auto",
    )
    fig.update_layout(
        title="Mean AQI by City × Year",
        xaxis_title="Year",
        yaxis_title="",
        height=max(400, len(pivot) * 28),
        coloraxis_colorbar_title="AQI",
    )
    return fig


# ── Page entry ───────────────────────────────────────────────────────────────
def render() -> None:
    page_header(
        "🏙️ City Pollution Ranking",
        "Which cities are the most polluted (highest average AQI) "
        "and which are the cleanest?",
    )

    raw = get_city_day()
    filters = render_filter_state(
        raw, key_prefix="cr_", show_pollutants=False, show_buckets=False,
    )
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    if df.empty:
        st.warning("No data available. Ensure `city_day.csv` is loaded.")
        return

    # Compute city rankings
    df_rank = city_mean_aqi(df)

    # --- KPIs ---------------------------------------------------------------
    section("Key Figures")
    if not df_rank.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏭 Most Polluted", df_rank.iloc[0][COL_CITY])
        col2.metric("AQI", f"{df_rank.iloc[0]['aqi_mean']:.1f}")
        col3.metric("🌿 Cleanest", df_rank.iloc[-1][COL_CITY])
        col4.metric("AQI", f"{df_rank.iloc[-1]['aqi_mean']:.1f}")

    # --- Top N slider -------------------------------------------------------
    section("Most Polluted vs Cleanest")
    top_n = st.slider(
        "Number of cities per group",
        min_value=3,
        max_value=min(13, len(df_rank) // 2) if len(df_rank) >= 6 else 3,
        value=min(10, len(df_rank) // 2) if len(df_rank) >= 6 else 3,
        key="cr_top_n",
    )
    show_chart(_top_bottom_bar(df_rank, top_n))

    # --- Full ranking -------------------------------------------------------
    section("Complete City Ranking")
    show_chart(_full_ranking_bar(df_rank))

    # --- Box-plot -----------------------------------------------------------
    section("AQI Distribution (Box-Plot)")
    st.caption("Compare spread and outliers across selected cities.")
    default_cities = (
        df_rank.head(3)[COL_CITY].tolist() + df_rank.tail(3)[COL_CITY].tolist()
        if len(df_rank) >= 6
        else df_rank[COL_CITY].tolist()
    )
    sel_cities = st.multiselect(
        "Pick cities",
        options=df_rank[COL_CITY].tolist(),
        default=default_cities,
        key="cr_box_cities",
    )
    if sel_cities:
        show_chart(_aqi_box_plot(df, sel_cities))
    else:
        st.info("Select at least one city above.")

    # --- Year × City heatmap ------------------------------------------------
    section("Mean AQI Heatmap (City × Year)")
    show_chart(_yearly_mean_heatmap(df))

    # --- Raw data table -----------------------------------------------------
    section("Data Table")
    with st.expander("Show full city ranking table"):
        st.dataframe(
            df_rank.rename(columns={"aqi_mean": "Mean AQI"}).reset_index(drop=True),
            use_container_width=True,
        )
