"""Pollutant correlation: AQI vs PM/NOx/SO2/CO (scaffold)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import correlation_heatmap, show_chart
from dashboard.components.filters import render_filter_state
from dashboard.data.schema import COL_AQI
from dashboard.data.transform import apply_filters
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day


def render() -> None:
    page_header(
        "Pollutant Correlation",
        "Correlations between AQI and selected pollutants; severe-period drivers (extend later).",
    )
    raw = get_city_day()
    filters = render_filter_state(raw, key_prefix="co_", show_pollutants=True, show_buckets=True)
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    section("Correlation matrix (Pearson)")
    heat_cols = [COL_AQI, *filters.pollutants]
    show_chart(correlation_heatmap(df, heat_cols))

    section("Severe episodes (proposal)")
    st.markdown(
        """
- **Planned**: filter rows where `AQI_Bucket == Severe` and compare mean pollutant levels.
- **Planned**: optional station-level view using `station_day.csv`.
        """
    )
    if not df.empty and "AQI_Bucket" in df.columns:
        severe = df[df["AQI_Bucket"].astype(str).str.contains("Severe", na=False)]
        st.metric("Severe rows (filtered)", len(severe))
        if len(severe) > 0 and filters.pollutants:
            means = severe[filters.pollutants].apply(pd.to_numeric, errors="coerce").mean()
            st.bar_chart(means)
