"""Insights: hotspot persistence and pollutant control priorities."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from dashboard.components.charts import (
    hotspot_duration_stacked_bar,
    hotspot_persistence_bar,
    metro_pollutant_priority_bar,
    metro_pollutant_priority_heatmap,
    show_chart,
)
from dashboard.components.filters import render_filter_state
from dashboard.data.transform import (
    apply_filters,
    hotspot_episode_duration_profile,
    hotspot_persistence_by_city,
    kpi_summary,
    pollutant_priority_matrix_for_metros,
    pollutant_priority_summary,
)
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day


def _render_hotspot_answer(profile_df: pd.DataFrame, persist_df: pd.DataFrame) -> None:
    if profile_df.empty or persist_df.empty:
        return

    totals = profile_df.groupby("duration_group", as_index=False)["episodes"].sum()
    total_episodes = int(totals["episodes"].sum())
    short_eps = int(totals.loc[totals["duration_group"] == "Short (<=3d)", "episodes"].sum())
    long_eps = int(totals.loc[totals["duration_group"] == "Long (>=8d)", "episodes"].sum())
    short_share = (100.0 * short_eps / total_episodes) if total_episodes else 0.0
    long_share = (100.0 * long_eps / total_episodes) if total_episodes else 0.0

    top_row = persist_df.iloc[0]
    top_city = str(top_row["City"])
    top_longest = int(top_row["longest_duration_days"])
    top_long_ratio = float(top_row["long_episode_ratio"] * 100)

    tendency = "mang tính ngắn hạn theo đợt" if short_share >= long_share else "có dấu hiệu kéo dài liên tục"

    with st.expander("Q1: Điểm nóng ô nhiễm là ngắn hạn hay kéo dài?", expanded=True):
        st.markdown(
            f"""
**Kết luận chính:** Ô nhiễm tại các điểm nóng **{tendency}** trong bộ lọc hiện tại.

- Tỷ trọng đợt ngắn (<=3 ngày): **{short_share:.1f}%**.
- Tỷ trọng đợt dài (>=8 ngày): **{long_share:.1f}%**.
- Thành phố có đợt kéo dài nổi bật nhất: **{top_city}** với đợt dài nhất **{top_longest} ngày**, tỷ lệ đợt dài **{top_long_ratio:.1f}%**.

Diễn giải: nếu tỷ lệ đợt ngắn cao, nên ưu tiên cảnh báo sớm và can thiệp theo đợt; nếu tỷ lệ đợt dài tăng, cần biện pháp kiểm soát phát thải nền theo chu kỳ dài hơn.
            """
        )


def _render_policy_answer(priority_df: pd.DataFrame) -> None:
    if priority_df.empty:
        return

    top3 = priority_df.head(3)
    names = ", ".join(top3["pollutant"].astype(str).tolist())
    first = top3.iloc[0]

    with st.expander("Q2: Nên ưu tiên kiểm soát chất ô nhiễm nào tại đô thị lớn?", expanded=True):
        st.markdown(
            f"""
**Khuyến nghị ưu tiên:** tập trung trước vào **{names}** để cải thiện AQI hiệu quả hơn trong các đô thị lớn.

- Chất đứng đầu: **{first['pollutant']}** (điểm ưu tiên **{first['priority_score']:.3f}**).
- |Tương quan với AQI| trung bình của chất đứng đầu: **{first['mean_abs_corr']:.3f}**.
- Mức tăng nồng độ trong các ngày AQI cao (severe uplift): **{first['mean_severe_lift']:.2f}x**.

Điểm ưu tiên được tổng hợp từ 2 thành phần lịch sử: độ liên hệ với AQI và mức tăng tương đối trong các ngày AQI rất cao.
            """
        )


def render() -> None:
    page_header(
        "Insights & Recommendations",
        "Hotspot duration patterns and pollutant-control priorities for major metros.",
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

    section("Câu hỏi 1: Điểm nóng là ngắn hạn hay kéo dài?")
    duration_profile = hotspot_episode_duration_profile(df, aqi_threshold=200, top_n=8)
    persistence = hotspot_persistence_by_city(df, aqi_threshold=200, top_n=8)
    if duration_profile.empty or persistence.empty:
        st.info("Không đủ dữ liệu để xây dựng đợt ô nhiễm theo điểm nóng trong bộ lọc hiện tại.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            show_chart(hotspot_duration_stacked_bar(duration_profile, threshold=200))
        with col2:
            show_chart(hotspot_persistence_bar(persistence))
        _render_hotspot_answer(duration_profile, persistence)

    section("Câu hỏi 2: Ưu tiên kiểm soát chất ô nhiễm nào ở đô thị lớn?")
    priority_matrix = pollutant_priority_matrix_for_metros(df, aqi_threshold=200, top_metros=8)
    priority_summary = pollutant_priority_summary(priority_matrix)
    if priority_matrix.empty or priority_summary.empty:
        st.info("Không đủ dữ liệu để tính mức ưu tiên chất ô nhiễm cho các đô thị lớn.")
    else:
        show_chart(metro_pollutant_priority_bar(priority_summary))
        show_chart(metro_pollutant_priority_heatmap(priority_matrix))
        st.dataframe(
            priority_summary.rename(
                columns={
                    "pollutant": "Chất ô nhiễm",
                    "priority_score": "Điểm ưu tiên",
                    "mean_abs_corr": "|Tương quan AQI| TB",
                    "mean_severe_lift": "Severe uplift TB",
                    "n_cities": "Số đô thị",
                }
            ),
            hide_index=True,
        )
        _render_policy_answer(priority_summary)

    section("Ghi chú phương pháp")
    st.caption(
        "Điểm nóng được xác định theo AQI >= 200; đợt ô nhiễm là chuỗi ngày liên tiếp vượt ngưỡng. "
        "Điểm ưu tiên chất ô nhiễm = 0.65 * chuẩn hóa |corr(AQI)| + 0.35 * chuẩn hóa severe uplift, "
        "tính riêng theo từng đô thị rồi lấy trung bình."
    )
