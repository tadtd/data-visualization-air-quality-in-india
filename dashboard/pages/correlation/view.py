"""Streamlit view for the Correlation page."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from dashboard.data.schema import COL_CITY
from dashboard.pages.correlation.charts import CorrelationCharts
from dashboard.pages.correlation.data import (
    POLLUTANT_COLUMNS,
    CorrelationData,
    MissingStrategy,
    SEVERE_BUCKET,
)
from dashboard.theme import chart_insight, section_divider


def render() -> None:
    """Render the Correlation page."""
    raw = st.session_state.get("shared_raw_df")
    filters = st.session_state.get("shared_filters")
    if raw is None or filters is None or raw.empty:
        st.warning("Thiếu hoặc rỗng file city_day.csv.")
        return

    missing_columns = CorrelationData.validate_required_columns(raw)
    if missing_columns:
        st.error(f"Thiếu các cột bắt buộc: {', '.join(missing_columns)}")
        return

    base_df = CorrelationData.prepare_base_data(raw)

    # --- Build city options for correlation-specific filter ---
    city_options = ["Tất cả thành phố"]
    if COL_CITY in base_df.columns:
        city_options += sorted(base_df[COL_CITY].dropna().astype(str).unique().tolist())

    # --- Heatmap + Controls+Scatter side by side ---
    heatmap_col, scatter_col = st.columns(2)

    with heatmap_col:
        selected_city = st.selectbox(
            "Thành phố (ma trận tương quan)",
            options=city_options, key="correlation_city",
        )

    with scatter_col:
        selected_pollutant = st.selectbox(
            "Chất ô nhiễm (biểu đồ phân tán)",
            options=POLLUTANT_COLUMNS, key="correlation_pollutant",
        )

    missing_strategy: MissingStrategy = st.sidebar.radio(
        "Xử lý giá trị thiếu",
        options=[
            "Drop rows with missing feature values",
            "Fill missing feature values with median",
        ],
        format_func=lambda s: "Bỏ dòng thiếu dữ liệu" if "Drop" in s else "Thay thế bằng trung vị",
        key="correlation_missing_strategy",
    )

    # Apply correlation-specific city filter
    corr_city = "All cities" if selected_city == "Tất cả thành phố" else selected_city
    filtered_df = CorrelationData.filter_data(
        base_df, corr_city, (filters.date_start, filters.date_end),
    )
    analysis_df = CorrelationData.handle_missing_values(filtered_df, missing_strategy)

    if analysis_df.empty:
        st.warning("Không còn dữ liệu sau khi lọc.")
        return

    correlation = CorrelationData.pearson_matrix(analysis_df)

    with heatmap_col:
        st.plotly_chart(CorrelationCharts.pearson_heatmap(correlation), width="stretch")
    with scatter_col:
        st.plotly_chart(CorrelationCharts.aqi_scatter(analysis_df, selected_pollutant), width="stretch")
    chart_insight("PM2.5 và PM10 thường có tương quan mạnh nhất với AQI — đây là hai chất ô nhiễm chính cần kiểm soát.")

    section_divider()

    # --- Severe contributors (use all-cities data for global insight) ---
    all_cities_df = CorrelationData.filter_data(
        base_df, "All cities", (filters.date_start, filters.date_end),
    )
    severe_means = CorrelationData.severe_pollutant_means(all_cities_df)
    severe_rows = int(all_cities_df["AQI_Bucket"].astype(str).eq(SEVERE_BUCKET).sum()) if "AQI_Bucket" in all_cities_df.columns else 0

    if severe_means.empty:
        st.info("Không có dữ liệu AQI mức Nguy hiểm trong khoảng thời gian đã chọn.")
    else:
        st.metric("Chất ô nhiễm đóng góp lớn nhất", str(severe_means.iloc[0]["Pollutant"]),
                   f"Trung bình: {severe_means.iloc[0]['Mean Value']:.1f} | Ngày nguy hiểm: {severe_rows}")
    st.plotly_chart(CorrelationCharts.severe_contributors_bar(severe_means), width="stretch")
    chart_insight("Vào những ngày AQI nguy hiểm, nồng độ PM2.5 thường tăng gấp nhiều lần so với mức trung bình.")

    section_divider()

    # --- Optional boxplot ---
    if st.checkbox("Hiển thị phân bố chất ô nhiễm theo mức AQI", key="correlation_show_bucket_boxplot"):
        st.plotly_chart(CorrelationCharts.bucket_boxplot(filtered_df), width="stretch")
