"""Streamlit view for the Temporal page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.filters import render_filter_state
from dashboard.data.loader import data_status_message
from dashboard.pages.temporal.charts import TemporalCharts
from dashboard.pages.temporal.data import TemporalData
from dashboard.theme import section_divider


def render() -> None:
    """Render the Temporal page."""
    st.sidebar.caption(data_status_message())
    raw = TemporalData.load_frame()
    filters = render_filter_state(raw, key_prefix="te_", show_pollutants=False, show_buckets=True)
    df = TemporalData.apply_filter_state(raw, filters)

    # --- Yearly + Monthly side by side ---
    yearly = TemporalData.yearly_aqi_mean(df)
    monthly = TemporalData.monthly_aqi_mean(df)
    col_annual, col_monthly = st.columns(2)
    with col_annual:
        show_chart(TemporalCharts.yearly_line(yearly))
    with col_monthly:
        show_chart(TemporalCharts.monthly_line(monthly))

    section_divider()

    # --- City small multiples ---
    city_monthly = TemporalData.monthly_aqi_by_city(df)
    if not city_monthly.empty:
        top6 = city_monthly.groupby("City")["aqi_mean"].mean().nlargest(6).index
        city_monthly = city_monthly[city_monthly["City"].isin(top6)]
    show_chart(TemporalCharts.city_small_multiples(city_monthly))

    section_divider()

    # --- Seasonality: winter KPIs + seasonal bar ---
    winter_summary = TemporalData.winter_vs_nonwinter(df)
    if not winter_summary.empty:
        winter_row = winter_summary[winter_summary["season"].str.startswith("Winter")]
        nonwinter_row = winter_summary[~winter_summary["season"].str.startswith("Winter")]
        winter_mean = float(winter_row["aqi_mean"].iloc[0]) if not winter_row.empty else None
        nonwinter_mean = float(nonwinter_row["aqi_mean"].iloc[0]) if not nonwinter_row.empty else None
        val_w = f"{winter_mean:.1f}" if winter_mean is not None else "—"
        val_n = f"{nonwinter_mean:.1f}" if nonwinter_mean is not None else "—"
        delta_str = (
            f"{winter_mean - nonwinter_mean:+.1f} vs non-winter"
            if (winter_mean is not None and nonwinter_mean is not None)
            else None
        )
        kpi_left, kpi_right = st.columns(2)
        kpi_left.metric(
            "Winter Mean AQI (Nov–Feb)",
            val_w,
            delta=delta_str,
            delta_color="inverse",
        )
        kpi_right.metric(
            "Non-Winter Mean AQI",
            val_n,
        )
    profile = TemporalData.seasonal_monthly_profile(df)
    show_chart(TemporalCharts.seasonal_profile(profile))

    section_divider()

    # --- Year-on-year comparison ---
    yoy = TemporalData.year_on_year_monthly(df)
    show_chart(TemporalCharts.year_on_year(yoy))

    section_divider()

    # --- City trend slopes ---
    slopes = TemporalData.city_trend_slopes(df)
    if slopes.empty:
        st.info("Not enough monthly data to compute city trends. Widen the date range.")
    else:
        show_chart(TemporalCharts.trend_slope_bar(slopes))

    section_divider()

    # --- Breach days ---
    breach_df = TemporalData.aqi_breach_count_by_year(df, threshold=200)
    show_chart(TemporalCharts.aqi_breach(breach_df, threshold=200))
