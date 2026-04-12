"""Streamlit view for the Overview page."""

from __future__ import annotations

import math

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.filters import render_filter_state
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data.loader import data_status_message
from dashboard.pages.overview.charts import OverviewCharts
from dashboard.pages.overview.data import OverviewData
from dashboard.theme import aqi_bucket_for_value, aqi_pill_html, hero_number_html, section_divider


def render() -> None:
    """Render the Overview page."""
    st.sidebar.caption(data_status_message())
    raw = OverviewData.load_frame()
    filters = render_filter_state(raw, key_prefix="ov_", show_pollutants=False, show_buckets=True)
    df = OverviewData.filter_frame(raw, filters)

    # --- Hero KPIs ---
    kpis = OverviewData.summarize_kpis(df)
    mean_v = kpis["mean_aqi"]
    mean_display = "—" if (kpis["rows"] == 0 or (isinstance(mean_v, float) and math.isnan(mean_v))) else round(mean_v, 1)
    bucket = aqi_bucket_for_value(mean_v if isinstance(mean_display, float) else None)

    hero_col, pill_col = st.columns([3, 1])
    with hero_col:
        st.markdown(hero_number_html(mean_display, bucket), unsafe_allow_html=True)
        st.markdown(f"National Average AQI &nbsp; {aqi_pill_html(bucket)}", unsafe_allow_html=True)
    with pill_col:
        st.caption(f"Filtered records: {kpis['rows']:,}")

    section_divider()

    worst_city, worst_aqi = OverviewData.most_polluted_city(df)
    best_city, best_aqi = OverviewData.cleanest_city(df)
    n_cities = OverviewData.city_count(df)

    render_kpi_row(
        {
            "Cities Monitored": n_cities,
            "Most Polluted": worst_aqi,
            "Cleanest City": best_aqi,
            "Median AQI": kpis["median_aqi"],
        },
        columns=4,
        subtitles={
            "Most Polluted": worst_city,
            "Cleanest City": best_city,
        },
    )

    section_divider()

    # --- Charts ---
    show_chart(OverviewCharts.monthly_trend(OverviewData.monthly_mean(df)))

    section_divider()

    show_chart(OverviewCharts.city_snapshot(OverviewData.city_mean(df), top_n=8))
