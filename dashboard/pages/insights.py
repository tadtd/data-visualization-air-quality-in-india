"""Insights & practical recommendations (narrative placeholders)."""

from __future__ import annotations

import streamlit as st
from dashboard.components.filters import render_filter_state
from dashboard.data.transform import apply_filters, kpi_summary
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day


def render() -> None:
    page_header(
        "Insights & Recommenrdations",
        "Short-term vs chronic hotspots and policy priorities — fill in after analysis.",
    )
    raw = get_city_day()
    filters = render_filter_state(raw, key_prefix="in_", show_pollutants=True, show_buckets=True)
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    section("Summary statistics (auto)")
    kpis = kpi_summary(df)
    st.write(
        {
            "mean_aqi": kpis["mean_aqi"],
            "median_aqi": kpis["median_aqi"],
            "n_records": kpis["rows"],
        }
    )

    section("Proposal-aligned questions")
    st.markdown(
        """
1. **Hotspots**: Are severe AQI events short spikes or sustained periods? *(Add duration analysis.)*
2. **Policy**: Which pollutants to prioritize in large metros to improve AQI? *(Use correlation + severe-period means.)*
        """
    )

    section("Discussion placeholders")
    st.info(
        "Document difficulties, limitations, and next steps here for the midterm report "
        "(What–Why–How + screenshots)."
    )
