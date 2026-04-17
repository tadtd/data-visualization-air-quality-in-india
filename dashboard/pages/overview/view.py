"""Streamlit view for the Overview page."""

from __future__ import annotations

import math

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.pages.overview.charts import OverviewCharts
from dashboard.pages.overview.data import OverviewData
from dashboard.theme import aqi_bucket_for_value, aqi_pill_html, chart_insight, hero_number_html, section_divider


def render() -> None:
    """Render the Overview page."""
    raw = st.session_state.get("shared_raw_df")
    filters = st.session_state.get("shared_filters")
    if raw is None or filters is None:
        st.warning("Dữ liệu chưa được tải.")
        return
    df = OverviewData.filter_frame(raw, filters)

    # --- Hero KPIs ---
    kpis = OverviewData.summarize_kpis(df)
    mean_v = kpis["mean_aqi"]
    mean_display = "—" if (kpis["rows"] == 0 or (isinstance(mean_v, float) and math.isnan(mean_v))) else round(mean_v, 1)
    bucket = aqi_bucket_for_value(mean_v if isinstance(mean_display, float) else None)

    hero_col, pill_col = st.columns([3, 1])
    with hero_col:
        st.markdown(hero_number_html(mean_display, bucket), unsafe_allow_html=True)
        st.markdown(f"AQI trung bình toàn quốc &nbsp; {aqi_pill_html(bucket)}", unsafe_allow_html=True)
    with pill_col:
        st.caption(f"Số bản ghi sau lọc: {kpis['rows']:,}")

    section_divider()

    worst_city, worst_aqi = OverviewData.most_polluted_city(df)
    best_city, best_aqi = OverviewData.cleanest_city(df)
    n_cities = OverviewData.city_count(df)

    render_kpi_row(
        {
            "Số thành phố": n_cities,
            "Ô nhiễm nhất": worst_aqi,
            "Sạch nhất": best_aqi,
            "AQI trung vị": kpis["median_aqi"],
        },
        columns=4,
        subtitles={
            "Ô nhiễm nhất": worst_city,
            "Sạch nhất": best_city,
        },
    )

    section_divider()

    # --- India Map ---
    city_coords = OverviewData.city_mean_with_coords(df)
    show_chart(OverviewCharts.india_map(city_coords))
    chart_insight("Kích thước và màu sắc vòng tròn thể hiện mức AQI trung bình — vòng càng lớn, ô nhiễm càng nặng.")

    section_divider()

    # --- Charts ---
    show_chart(OverviewCharts.monthly_trend(OverviewData.monthly_mean(df)))
    chart_insight("AQI thường tăng mạnh vào mùa đông (tháng 11–2) do nghịch nhiệt và đốt rơm rạ.")

    section_divider()

    show_chart(OverviewCharts.city_snapshot(OverviewData.city_mean(df), top_n=8))
    chart_insight("Delhi và các thành phố miền Bắc luôn dẫn đầu về mức ô nhiễm, trong khi miền Nam sạch hơn đáng kể.")
