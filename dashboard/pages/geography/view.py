"""Streamlit view for the Geography page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.filters import render_filter_state
from dashboard.data.loader import data_status_message
from dashboard.pages.geography.charts import GeographyCharts
from dashboard.pages.geography.data import GeographyData
from dashboard.theme import section_divider


def render() -> None:
    """Render the Geography page."""
    st.sidebar.caption(data_status_message())
    raw = GeographyData.load_frame()
    filters = render_filter_state(raw, key_prefix="geo_", show_pollutants=False, show_buckets=True)
    df = GeographyData.filter_frame(raw, filters)

    show_chart(GeographyCharts.city_mean_ranking(GeographyData.city_mean(df), top_n=10))

    section_divider()

    show_chart(GeographyCharts.dangerous_days(GeographyData.dangerous_day_counts(df), top_n=15))

    section_divider()

    state_df = GeographyData.state_mean(df)
    if not state_df.empty:
        show_chart(GeographyCharts.state_ranking_bar(state_df))
    else:
        st.info("State-level data requires stations.csv. Place it in the data directory.")
