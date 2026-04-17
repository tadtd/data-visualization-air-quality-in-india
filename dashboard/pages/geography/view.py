"""Geography tab: city ranking + danger frequency in one page (streamlined)."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import show_chart
from dashboard.config import DANGEROUS_AQI_BUCKETS
from dashboard.data.schema import COL_AQI_BUCKET, COL_CITY
from dashboard.data.transforms import count_dangerous_days_by_city
from dashboard.pages.geography.charts import GeographyCharts
from dashboard.pages.geography.data import GeographyData
from dashboard.theme import chart_insight, section_divider


def render() -> None:
    raw = st.session_state.get("shared_raw_df")
    filters = st.session_state.get("shared_filters")
    if raw is None or filters is None:
        st.warning("Dữ liệu chưa được tải.")
        return
    df = GeographyData.filter_frame(raw, filters)

    if df.empty:
        st.warning("Không có dữ liệu. Hãy đảm bảo file `city_day.csv` đã được tải.")
        return

    df_rank = GeographyData.city_mean(df)

    # ── Xếp hạng thành phố ──────────────────────────────────────────
    st.header("🏙️ Xếp hạng ô nhiễm theo thành phố")

    if not df_rank.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ô nhiễm nhất", df_rank.iloc[0][COL_CITY])
        col2.metric("AQI", f"{df_rank.iloc[0]['aqi_mean']:.1f}")
        col3.metric("Sạch nhất", df_rank.iloc[-1][COL_CITY])
        col4.metric("AQI", f"{df_rank.iloc[-1]['aqi_mean']:.1f}")

    section_divider()

    n_cities = len(df_rank)
    if n_cities >= 6:
        slider_min = 3
        slider_max = max(slider_min + 1, min(13, n_cities // 2))
        slider_val = min(10, n_cities // 2)
        slider_val = max(slider_min, min(slider_val, slider_max))
        top_n = st.slider(
            "Số thành phố mỗi nhóm",
            min_value=slider_min,
            max_value=slider_max,
            value=slider_val,
            key="geo_cr_top_n",
        )
    else:
        top_n = n_cities  # too few cities to split
    show_chart(GeographyCharts.top_bottom_polluted_clean(df_rank, top_n))
    chart_insight("Chênh lệch AQI giữa thành phố ô nhiễm nhất và sạch nhất có thể lên tới 4–5 lần.")

    section_divider()

    show_chart(GeographyCharts.full_city_ranking_bar(df_rank))

    section_divider()

    # Box-plot
    st.subheader("Phân bố AQI hàng ngày")
    default_cities = (
        df_rank.head(3)[COL_CITY].tolist() + df_rank.tail(3)[COL_CITY].tolist()
        if len(df_rank) >= 6
        else df_rank[COL_CITY].tolist()
    )
    sel_cities = st.multiselect(
        "Chọn thành phố",
        options=df_rank[COL_CITY].tolist(),
        default=default_cities,
        key="geo_cr_box_cities",
    )
    if sel_cities:
        show_chart(GeographyCharts.aqi_box_by_cities(df, sel_cities))
        chart_insight("Hộp rộng cho thấy chất lượng không khí biến động lớn trong ngày — đặc biệt ở các thành phố miền Bắc.")
    else:
        st.info("Chọn ít nhất một thành phố ở trên.")

    section_divider()

    show_chart(GeographyCharts.yearly_mean_aqi_heatmap(df))
    chart_insight("Heatmap cho thấy xu hướng cải thiện hoặc xấu đi theo thời gian của từng thành phố.")

    # ── Tần suất ô nhiễm nguy hiểm ──────────────────────────────────
    section_divider()
    st.header("⚠️ Tần suất ô nhiễm nguy hiểm")

    danger = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)]
    total_records = len(df[df[COL_AQI_BUCKET].notna()])
    danger_count = len(danger)
    ddc = count_dangerous_days_by_city(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng ngày nguy hiểm", f"{danger_count:,}")
    col2.metric(
        "Tỉ lệ nguy hiểm",
        f"{danger_count / total_records * 100:.1f}%" if total_records else "—",
    )
    if not ddc.empty:
        col3.metric("Thành phố tệ nhất", ddc.iloc[0][COL_CITY])
    else:
        col3.metric("Thành phố tệ nhất", "—")

    section_divider()

    show_chart(GeographyCharts.stacked_dangerous_days_by_city(df))
    chart_insight("Các thành phố miền Bắc Ấn Độ chịu phần lớn số ngày ô nhiễm ở mức nguy hiểm.")

    section_divider()

    show_chart(GeographyCharts.dangerous_bucket_pct_bar(df))
    chart_insight("Tỉ lệ ngày 'Nguy hiểm' vs 'Rất kém' vs 'Kém' khác nhau đáng kể giữa các thành phố.")

    section_divider()

    show_chart(GeographyCharts.dangerous_days_yearly_trend(df))
    chart_insight("Năm 2020 ghi nhận giảm mạnh nhờ phong tỏa COVID-19, nhưng xu hướng có thể đảo ngược.")
