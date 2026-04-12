"""Derived insights for the Correlation page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data.schema import COL_AQI
from dashboard.pages.correlation.data import GAS_COLUMNS, PARTICULATE_COLUMNS, POLLUTANT_COLUMNS


class CorrelationInsights:
    """Derived statistics and copy helpers for the policy section."""

    @staticmethod
    def aqi_column_correlations(corr: pd.DataFrame) -> pd.Series:
        if corr.empty or COL_AQI not in corr.columns:
            return pd.Series(dtype="float64")
        aqi_corr = pd.to_numeric(corr[COL_AQI], errors="coerce")
        aqi_corr = aqi_corr.reindex(POLLUTANT_COLUMNS).dropna()
        return aqi_corr.sort_values(ascending=False)

    @staticmethod
    def mean_for_columns(series: pd.Series, columns: tuple[str, ...]) -> float | None:
        if series.empty:
            return None
        values = pd.to_numeric(series.reindex(columns), errors="coerce").dropna()
        if values.empty:
            return None
        return float(values.mean())

    @staticmethod
    def sum_for_columns(series: pd.Series, columns: tuple[str, ...]) -> float | None:
        if series.empty:
            return None
        values = pd.to_numeric(series.reindex(columns), errors="coerce").dropna()
        if values.empty:
            return None
        return float(values.sum())

    @staticmethod
    def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator in (None, 0):
            return None
        return float(numerator / denominator)

    @staticmethod
    def fmt(value: float | None, precision: int = 2) -> str:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{value:.{precision}f}"


def render_policy_summary(correlation: pd.DataFrame, severe_means: pd.DataFrame) -> None:
    """Render concise Vietnamese insights from correlation and Severe means."""
    st.markdown("---")
    st.subheader("Insights dành cho nhà hoạch định chính sách")

    aqi_corr = CorrelationInsights.aqi_column_correlations(correlation)
    severe_series = (
        pd.Series(dtype="float64")
        if severe_means.empty
        else severe_means.set_index("Pollutant")["Mean Value"]
    )

    if aqi_corr.empty and severe_series.empty:
        st.info("Chưa đủ dữ liệu để tạo insight cho bộ lọc hiện tại.")
        return

    strongest_pollutant = str(aqi_corr.index[0]) if not aqi_corr.empty else "N/A"
    strongest_r = float(aqi_corr.iloc[0]) if not aqi_corr.empty else None
    pm_corr_mean = CorrelationInsights.mean_for_columns(aqi_corr, PARTICULATE_COLUMNS)
    gas_corr_mean = CorrelationInsights.mean_for_columns(aqi_corr, GAS_COLUMNS)
    pm_vs_gas_corr_ratio = CorrelationInsights.safe_ratio(pm_corr_mean, gas_corr_mean)
    dominant_pollutant = (
        str(severe_series.sort_values(ascending=False).index[0]) if not severe_series.empty else "N/A"
    )
    dominant_value = (
        float(severe_series.sort_values(ascending=False).iloc[0]) if not severe_series.empty else None
    )
    pm_severe_total = CorrelationInsights.sum_for_columns(severe_series, PARTICULATE_COLUMNS)
    gas_severe_total = CorrelationInsights.sum_for_columns(severe_series, GAS_COLUMNS)
    pm_vs_gas_severe_ratio = CorrelationInsights.safe_ratio(pm_severe_total, gas_severe_total)

    policy_recommendation = (
        "Ưu tiên ngân sách ngắn hạn cho kiểm soát bụi (PM10/PM2.5): kiểm soát bụi đường, công trình và xe tải nặng; "
        "kích hoạt kịch bản ứng phó theo ngưỡng Severe tại điểm nóng đô thị."
        if strongest_pollutant in PARTICULATE_COLUMNS
        else "Tăng cường kiểm soát nguồn khí chi phối (đặc biệt NO2/SO2/CO) kết hợp cảnh báo sớm theo ngưỡng Severe."
    )

    fmt = CorrelationInsights.fmt
    with st.expander("Tóm tắt phân tích cho nhà hoạch định", expanded=True):
        st.markdown(
            f"""
1. **Chất ảnh hưởng AQI mạnh nhất:** {strongest_pollutant} với hệ số tương quan Pearson **r = {fmt(strongest_r, 3)}**.

2. **So sánh bụi hạt và khí:** tương quan trung bình nhóm PM là **{fmt(pm_corr_mean, 3)}**, nhóm khí là **{fmt(gas_corr_mean, 3)}**; PM cao hơn khoảng **{fmt(pm_vs_gas_corr_ratio, 2)} lần**.

3. **Chất trội trong điều kiện Severe:** {dominant_pollutant} với giá trị trung bình **{fmt(dominant_value, 2)}**. Tổng PM trên ngày Severe cao khoảng **{fmt(pm_vs_gas_severe_ratio, 2)} lần** tổng nhóm khí.

4. **Khuyến nghị hành động:** {policy_recommendation}
            """
        )
