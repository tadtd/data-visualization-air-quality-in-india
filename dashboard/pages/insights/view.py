"""Streamlit view for the Insights page — visual-first, no narrative text."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.pages.insights.charts import InsightsCharts
from dashboard.pages.insights.data import InsightsData
from dashboard.theme import chart_insight, section_divider


def render() -> None:
    """Render the Insights page."""
    raw = st.session_state.get("shared_raw_df")
    filters = st.session_state.get("shared_filters")
    if raw is None or filters is None:
        st.warning("Dữ liệu chưa được tải.")
        return
    df = InsightsData.filter_frame(raw, filters)

    # --- Hotspot duration ---
    duration_profile = InsightsData.hotspot_duration_profile(df, aqi_threshold=200, top_n=8)
    persistence = InsightsData.hotspot_persistence_by_city(df, aqi_threshold=200, top_n=8)
    if duration_profile.empty or persistence.empty:
        st.info("Không đủ dữ liệu để phân tích các đợt ô nhiễm nặng với bộ lọc hiện tại.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            show_chart(InsightsCharts.hotspot_duration_stacked(duration_profile, threshold=200))
        with col2:
            show_chart(InsightsCharts.hotspot_persistence(persistence))
        chart_insight("Đợt ô nhiễm kéo dài ≥8 ngày tập trung ở các thành phố miền Bắc — cho thấy ô nhiễm mang tính hệ thống, không phải ngẫu nhiên.")

    section_divider()

    # --- Pollutant priority ---
    priority_matrix = InsightsData.pollutant_priority_matrix(df, aqi_threshold=200, top_metros=8)
    priority_summary = InsightsData.pollutant_priority_summary(priority_matrix)
    if priority_matrix.empty or priority_summary.empty:
        st.info("Không đủ dữ liệu để tính mức ưu tiên kiểm soát chất ô nhiễm.")
    else:
        show_chart(InsightsCharts.metro_priority_bar(priority_summary))
        chart_insight("PM2.5 luôn đứng đầu bảng ưu tiên — kiểm soát bụi mịn là biện pháp hiệu quả nhất để cải thiện AQI.")

        section_divider()

        show_chart(InsightsCharts.metro_priority_heatmap(priority_matrix))
        chart_insight("Mức ưu tiên khác nhau theo thành phố — cần chính sách riêng cho từng khu vực.")

    section_divider()

    # --- Methodology (collapsed) ---
    with st.expander("Về dữ liệu này", expanded=False):
        st.caption(
            "Điểm nóng ô nhiễm được xác định khi AQI ≥ 200; các đợt ô nhiễm là chuỗi ngày liên tiếp vượt ngưỡng. "
            "Điểm ưu tiên kiểm soát = 0.65 × |tương quan AQI| chuẩn hóa + 0.35 × mức tăng khi nguy hiểm chuẩn hóa, "
            "tính theo từng thành phố rồi lấy trung bình. "
            "Nguồn dữ liệu: Air Quality Data in India (2015–2020) từ Kaggle."
        )
