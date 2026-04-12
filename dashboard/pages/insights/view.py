"""Streamlit view for the Insights page — visual-first, no narrative text."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.filters import render_filter_state
from dashboard.data.loader import data_status_message
from dashboard.pages.insights.charts import InsightsCharts
from dashboard.pages.insights.data import InsightsData
from dashboard.theme import section_divider


def render() -> None:
    """Render the Insights page."""
    st.sidebar.caption(data_status_message())
    raw = InsightsData.load_frame()
    filters = render_filter_state(raw, key_prefix="in_", show_pollutants=True, show_buckets=True)
    df = InsightsData.apply_filter_state(raw, filters)

    # --- Hotspot duration ---
    duration_profile = InsightsData.hotspot_duration_profile(df, aqi_threshold=200, top_n=8)
    persistence = InsightsData.hotspot_persistence_by_city(df, aqi_threshold=200, top_n=8)
    if duration_profile.empty or persistence.empty:
        st.info("Not enough data to build hotspot episodes for current filters.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            show_chart(InsightsCharts.hotspot_duration_stacked(duration_profile, threshold=200))
        with col2:
            show_chart(InsightsCharts.hotspot_persistence(persistence))

    section_divider()

    # --- Pollutant priority ---
    priority_matrix = InsightsData.pollutant_priority_matrix(df, aqi_threshold=200, top_metros=8)
    priority_summary = InsightsData.pollutant_priority_summary(priority_matrix)
    if priority_matrix.empty or priority_summary.empty:
        st.info("Not enough data to compute pollutant priorities for major cities.")
    else:
        show_chart(InsightsCharts.metro_priority_bar(priority_summary))

        section_divider()

        show_chart(InsightsCharts.metro_priority_heatmap(priority_matrix))

    section_divider()

    # --- Methodology (collapsed) ---
    with st.expander("About this data", expanded=False):
        st.caption(
            "Hotspots are identified by AQI >= 200; episodes are consecutive days above the threshold. "
            "Pollutant priority score = 0.65 × normalized |corr(AQI)| + 0.35 × normalized severe uplift, "
            "computed per city then averaged. "
            "Data source: Air Quality Data in India (2015–2020) from Kaggle."
        )
