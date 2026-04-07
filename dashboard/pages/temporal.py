"""Temporal analysis: trends, seasonality, city comparison (scaffold)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import monthly_aqi_line, show_chart
from dashboard.components.filters import render_filter_state
from dashboard.data.transform import apply_filters, city_mean_aqi, monthly_aqi_mean
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day


def render() -> None:
    page_header(
        "Temporal Analysis",
        "AQI over months/years, seasonality, and city trend comparison (extend with more charts).",
    )
    raw = get_city_day()
    filters = render_filter_state(raw, key_prefix="te_", show_pollutants=False, show_buckets=True)
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    section("AQI trend (monthly mean)")
    m = monthly_aqi_mean(df)
    show_chart(monthly_aqi_line(m))

    section("City-level mean AQI (filtered window)")
    c = city_mean_aqi(df)
    if not c.empty:
        st.dataframe(c.head(20), width='stretch')
    else:
        st.info("Load `city_day.csv` to see city trends.")

    section("Seasonality (proposal)")
    st.markdown(
        """
- **Planned**: monthly/season aggregation, winter vs non-winter comparison.
- **Planned**: slope / trend per city (improving vs worsening).
        """
    )
    if not df.empty and "Date" in df.columns:
        t = df.copy()
        t["Date"] = pd.to_datetime(t["Date"], errors="coerce")
        t = t.dropna(subset=["Date"])
        t["month"] = t["Date"].dt.month
        if "AQI" in t.columns:
            seasonal = t.groupby("month", as_index=False)["AQI"].mean()
            st.line_chart(seasonal.set_index("month"))
