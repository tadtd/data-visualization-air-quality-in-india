"""Streamlit view for the Temporal page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.pages.temporal.charts import TemporalCharts
from dashboard.pages.temporal.data import TemporalData
from dashboard.theme import chart_insight, section_divider


def render() -> None:
    """Render the Temporal page."""
    raw = st.session_state.get("shared_raw_df")
    filters = st.session_state.get("shared_filters")
    if raw is None or filters is None:
        st.warning("Dữ liệu chưa được tải.")
        return
    df = TemporalData.filter_frame(raw, filters)

    # --- Yearly + Monthly side by side ---
    yearly = TemporalData.yearly_aqi_mean(df)
    monthly = TemporalData.monthly_aqi_mean(df)
    col_annual, col_monthly = st.columns(2)
    with col_annual:
        show_chart(TemporalCharts.yearly_line(yearly))
    with col_monthly:
        show_chart(TemporalCharts.monthly_line(monthly))
    chart_insight("AQI có xu hướng giảm nhẹ từ 2017, giảm mạnh năm 2020 do phong tỏa COVID-19.")

    section_divider()

    # --- City small multiples ---
    city_monthly = TemporalData.monthly_aqi_by_city(df)
    if not city_monthly.empty:
        top6 = city_monthly.groupby("City")["aqi_mean"].mean().nlargest(6).index
        city_monthly = city_monthly[city_monthly["City"].isin(top6)]
    show_chart(TemporalCharts.city_small_multiples(city_monthly))
    chart_insight("Mỗi thành phố có biên độ dao động AQI khác nhau — Delhi biến động lớn nhất.")

    section_divider()

    # --- Seasonality: winter KPIs + seasonal bar ---
    winter_summary = TemporalData.winter_vs_nonwinter(df)
    if not winter_summary.empty:
        winter_row = winter_summary[winter_summary["season"].str.startswith("Winter")]
        nonwinter_row = winter_summary[~winter_summary["season"].str.startswith("Winter")]
        winter_mean = float(winter_row["aqi_mean"].iloc[0]) if not winter_row.empty else None
        nonwinter_mean = float(nonwinter_row["aqi_mean"].iloc[0]) if not nonwinter_row.empty else None
        val_w = f"{winter_mean:.1f}" if winter_mean is not None else "—"
        val_n = f"{nonwinter_mean:.1f}" if nonwinter_mean is not None else "—"
        delta_str = (
            f"{winter_mean - nonwinter_mean:+.1f} so với ngoài mùa đông"
            if (winter_mean is not None and nonwinter_mean is not None)
            else None
        )
        kpi_left, kpi_right = st.columns(2)
        kpi_left.metric(
            "AQI mùa đông (T11–T2)",
            val_w,
            delta=delta_str,
            delta_color="inverse",
        )
        kpi_right.metric(
            "AQI ngoài mùa đông",
            val_n,
        )
    profile = TemporalData.seasonal_monthly_profile(df)
    show_chart(TemporalCharts.seasonal_profile(profile))
    chart_insight("Mùa đông (tháng 11–2) AQI cao hơn rõ rệt do nghịch nhiệt và đốt rơm rạ.")

    section_divider()

    # --- Year-on-year comparison ---
    yoy = TemporalData.year_on_year_monthly(df)
    show_chart(TemporalCharts.year_on_year(yoy))

    section_divider()

    # --- City trend slopes ---
    slopes = TemporalData.city_trend_slopes(df)
    if slopes.empty:
        st.info("Không đủ dữ liệu hàng tháng để tính xu hướng. Hãy mở rộng khoảng thời gian.")
    else:
        show_chart(TemporalCharts.trend_slope_bar(slopes))
        chart_insight("Giá trị âm = cải thiện, giá trị dương = xấu đi. Nhiều thành phố miền Nam có xu hướng cải thiện.")

    section_divider()

    # --- Breach days ---
    breach_df = TemporalData.aqi_breach_count_by_year(df, threshold=200)
    show_chart(TemporalCharts.aqi_breach(breach_df, threshold=200))
    chart_insight("Số ngày AQI vượt ngưỡng 200 giảm đáng kể trong năm 2020.")
