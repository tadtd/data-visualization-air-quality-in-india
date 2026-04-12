"""Geography tab: former city_ranking + danger_frequency dashboards in one page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.filters import render_filter_state
from dashboard.data.loader import data_status_message
from dashboard.config import DANGEROUS_AQI_BUCKETS
from dashboard.data.schema import COL_AQI_BUCKET, COL_CITY
from dashboard.data.transforms import count_dangerous_days_by_city
from dashboard.layout import section
from dashboard.pages.geography.charts import GeographyCharts
from dashboard.pages.geography.data import GeographyData


def render() -> None:
    st.sidebar.caption(data_status_message())
    raw = GeographyData.load_frame()
    filters = render_filter_state(raw, key_prefix="geo_", show_pollutants=False, show_buckets=True)
    df = GeographyData.filter_frame(raw, filters)

    if df.empty:
        st.warning("No data available. Ensure `city_day.csv` is loaded.")
        return

    df_rank = GeographyData.city_mean(df)

    # ----- Former city_ranking.py -------------------------------------------
    st.header("City pollution ranking")
    st.caption(
        "Which cities are the most polluted (highest average AQI) and which are the cleanest?"
    )

    section("Key Figures")
    if not df_rank.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Most Polluted", df_rank.iloc[0][COL_CITY])
        col2.metric("AQI", f"{df_rank.iloc[0]['aqi_mean']:.1f}")
        col3.metric("Cleanest", df_rank.iloc[-1][COL_CITY])
        col4.metric("AQI", f"{df_rank.iloc[-1]['aqi_mean']:.1f}")

    section("Most Polluted vs Cleanest")
    top_n = st.slider(
        "Number of cities per group",
        min_value=3,
        max_value=min(13, len(df_rank) // 2) if len(df_rank) >= 6 else 3,
        value=min(10, len(df_rank) // 2) if len(df_rank) >= 6 else 3,
        key="geo_cr_top_n",
    )
    show_chart(GeographyCharts.top_bottom_polluted_clean(df_rank, top_n))

    section("Complete City Ranking")
    show_chart(GeographyCharts.full_city_ranking_bar(df_rank))

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
        key="geo_cr_box_cities",
    )
    if sel_cities:
        show_chart(GeographyCharts.aqi_box_by_cities(df, sel_cities))
    else:
        st.info("Select at least one city above.")

    section("Mean AQI Heatmap (City × Year)")
    show_chart(GeographyCharts.yearly_mean_aqi_heatmap(df))

    section("Data Table")
    with st.expander("Show full city ranking table"):
        st.dataframe(
            df_rank.rename(columns={"aqi_mean": "Mean AQI"}).reset_index(drop=True),
            width='stretch',
        )

    # ----- Former danger_frequency.py ---------------------------------------
    st.header("Dangerous pollution frequency")
    st.caption(
        "How are dangerous AQI days (Poor, Very Poor, Severe) distributed across cities?"
    )

    section("Key Figures")
    danger = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)]
    total_records = len(df[df[COL_AQI_BUCKET].notna()])
    danger_count = len(danger)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records (with label)", f"{total_records:,}")
    col2.metric("Dangerous Days Total", f"{danger_count:,}")
    col3.metric(
        "Dangerous %",
        f"{danger_count / total_records * 100:.1f}%" if total_records else "—",
    )
    ddc = count_dangerous_days_by_city(df)
    if not ddc.empty:
        col4.metric("Worst City", ddc.iloc[0][COL_CITY])
    else:
        col4.metric("Worst City", "—")

    section("Stacked Bar — All Cities")
    show_chart(GeographyCharts.stacked_dangerous_days_by_city(df))

    section("Grouped Comparison (Top N)")
    n_u = int(df[COL_CITY].nunique()) if COL_CITY in df.columns else 1
    hi_g = min(26, max(1, n_u))
    lo_g = min(5, hi_g)
    top_n_df = st.slider(
        "Number of cities to show",
        min_value=lo_g,
        max_value=hi_g,
        value=min(15, hi_g),
        key="geo_df_top_n",
    )
    show_chart(GeographyCharts.grouped_dangerous_days_by_city(df, top_n_df))

    section("Proportion Breakdown (%)")
    st.caption(
        "Among dangerous days only — what proportion falls into "
        "Poor vs Very Poor vs Severe for each city?"
    )
    show_chart(GeographyCharts.dangerous_bucket_pct_bar(df))

    section("Heatmap (City × Bucket)")
    show_chart(GeographyCharts.dangerous_city_bucket_heatmap(df))

    section("Yearly Trend of Dangerous Days")
    show_chart(GeographyCharts.dangerous_days_yearly_trend(df))

    section("Data Table")
    with st.expander("Show dangerous day counts by city"):
        st.dataframe(
            ddc.rename(columns={"danger_days": "Dangerous Days"}).reset_index(drop=True),
            width='stretch',
        )
