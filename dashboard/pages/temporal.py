"""Temporal analysis: trends, seasonality, city comparison (scaffold)."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import (
    aqi_breach_bar,
    city_small_multiples_line,
    city_trend_slope_bar,
    monthly_aqi_line,
    seasonal_profile_bar,
    show_chart,
    yearly_aqi_line,
)
from dashboard.components.filters import render_filter_state
from dashboard.data.transform import (
    apply_filters,
    aqi_breach_count_by_year,
    city_trend_slopes,
    monthly_aqi_by_city,
    monthly_aqi_mean,
    seasonal_monthly_profile,
    winter_vs_nonwinter,
    yearly_aqi_mean,
)
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day


def render_what_why_how() -> None:
    """Analysis framing expander — three questions in Vietnamese only."""
    with st.expander("Mục tiêu phân tích", expanded=True):
        st.markdown(
            """
**Câu hỏi 1 — AQI trung bình biến động như thế nào theo tháng và theo năm trong giai đoạn 2015–2020?**
- **Mục tiêu:** Phân tích sự biến động của chỉ số AQI trung bình theo từng tháng và từng năm trong giai đoạn 2015–2020.
- **Lý do:** Nắm bắt xu hướng AQI dài hạn và theo tháng giúp xác định chất lượng không khí đang cải thiện, xấu đi hay duy trì ổn định theo thời gian.
- **Phương pháp:** Lọc dữ liệu theo thành phố và khoảng thời gian đã chọn, tổng hợp AQI theo tháng và năm, trực quan hoá bằng biểu đồ đường theo tháng hoặc biểu đồ tổng hợp theo năm.

**Câu hỏi 2 — Có xuất hiện tính mùa vụ trong ô nhiễm không khí hay không?**
- **Mục tiêu:** Kiểm tra xem mức độ ô nhiễm không khí có biến động theo mùa hay không, đặc biệt là hiện tượng đỉnh ô nhiễm vào mùa đông.
- **Lý do:** Các mô hình ô nhiễm theo mùa phản ánh các yếu tố môi trường và hoạt động con người như đốt rơm rạ, nghịch nhiệt nhiệt độ hoặc thói quen sử dụng năng lượng.
- **Phương pháp:** Nhóm dữ liệu AQI theo tháng lịch, tính AQI trung bình từng tháng trong toàn bộ giai đoạn, trực quan hoá bằng biểu đồ thanh theo mùa với phân biệt mùa đông và các tháng còn lại.

**Câu hỏi 3 — Thành phố nào đang cải thiện chất lượng không khí và thành phố nào đang trở nên ô nhiễm hơn theo thời gian?**
- **Mục tiêu:** Xác định các thành phố có xu hướng AQI cải thiện hoặc xấu đi trong giai đoạn 2015–2020.
- **Lý do:** Phát hiện xu hướng cấp thành phố giúp đánh giá hiệu quả của các chính sách môi trường và xác định các điểm nóng ô nhiễm cần ưu tiên can thiệp.
- **Phương pháp:** Tính hệ số hồi quy tuyến tính của AQI theo thời gian cho từng thành phố, phân loại thành cải thiện, xấu đi hoặc ổn định, trực quan hoá bằng biểu đồ thanh phân kỳ và bảng xếp hạng.
            """
        )


def _render_qa_trend(yearly: "pd.DataFrame", monthly: "pd.DataFrame") -> None:
    """Q&A block for Question 1 — placed below the AQI trend charts."""
    lines: list[str] = []

    if not yearly.empty and len(yearly) >= 2:
        first_year = int(yearly["year"].iloc[0])
        last_year = int(yearly["year"].iloc[-1])
        first_aqi = float(yearly["aqi_mean"].iloc[0])
        last_aqi = float(yearly["aqi_mean"].iloc[-1])
        delta = last_aqi - first_aqi
        direction = "tăng" if delta > 0 else "giảm"
        lines.append(
            f"- AQI trung bình {direction} từ <b>{first_aqi:.1f}</b> ({first_year}) "
            f"xuống còn <b>{last_aqi:.1f}</b> ({last_year}), "
            f"mức thay đổi <b>{abs(delta):.1f}</b> đơn vị trong toàn giai đoạn."
        )

    if not yearly.empty:
        best_idx = yearly["aqi_mean"].idxmin()
        worst_idx = yearly["aqi_mean"].idxmax()
        best_year = int(yearly.loc[best_idx, "year"])
        best_val = float(yearly.loc[best_idx, "aqi_mean"])
        worst_year = int(yearly.loc[worst_idx, "year"])
        worst_val = float(yearly.loc[worst_idx, "aqi_mean"])
        lines.append(
            f"- Năm <b>{best_year}</b> ghi nhận AQI thấp nhất (<b>{best_val:.1f}</b>); "
            f"năm <b>{worst_year}</b> có mức cao nhất (<b>{worst_val:.1f}</b>) — "
            f"chênh lệch <b>{worst_val - best_val:.1f}</b> đơn vị."
        )

    if not monthly.empty:
        peak_idx = monthly["aqi_mean"].idxmax()
        peak_month = str(monthly.loc[peak_idx, "year_month"])
        peak_val = float(monthly.loc[peak_idx, "aqi_mean"])
        lines.append(
            f"- Tháng có AQI cao nhất trong toàn giai đoạn là <b>{peak_month}</b> "
            f"(<b>{peak_val:.1f}</b>), phản ánh biến động ngắn hạn do mùa vụ và các sự kiện ô nhiễm cục bộ."
        )

    if not lines:
        return
    q = "AQI trung bình biến động như thế nào theo tháng và theo năm trong giai đoạn 2015–2020?"
    items = "".join(f"<li>{ln.lstrip('- ')}</li>" for ln in lines)
    with st.expander("Q1: AQI trung bình biến động theo tháng và năm (2015–2020)"):
        st.markdown(
            f"<h3>Câu hỏi</h3>"
            f"<p style='font-size:18px;'>{q}</p>"
            f"<h3>Trả lời</h3>"
            f"<ul style='font-size:18px;'>{items}</ul>",
            unsafe_allow_html=True,
        )


def _render_qa_seasonality(wvn: "pd.DataFrame", profile: "pd.DataFrame") -> None:
    """Q&A block for Question 2 — placed below the seasonality chart."""
    lines: list[str] = []

    if not wvn.empty:
        winter_row = wvn[wvn["season"].str.startswith("Winter")]
        nonwinter_row = wvn[~wvn["season"].str.startswith("Winter")]
        if not winter_row.empty and not nonwinter_row.empty:
            w = float(winter_row["aqi_mean"].iloc[0])
            nw = float(nonwinter_row["aqi_mean"].iloc[0])
            pct = (w - nw) / nw * 100
            lines.append(
                f"- Các tháng mùa đông (tháng 11–2) có AQI trung bình <b>{w:.1f}</b>, "
                f"cao hơn <b>{pct:.1f}%</b> so với các tháng còn lại (<b>{nw:.1f}</b>), "
                f"xác nhận tính mùa vụ rõ rệt trong ô nhiễm không khí."
            )

    if not profile.empty:
        peak_idx = profile["aqi_mean"].idxmax()
        peak_month = profile.loc[peak_idx, "month_name"]
        peak_val = float(profile.loc[peak_idx, "aqi_mean"])
        low_idx = profile["aqi_mean"].idxmin()
        low_month = profile.loc[low_idx, "month_name"]
        low_val = float(profile.loc[low_idx, "aqi_mean"])
        lines.append(
            f"- Tháng {peak_month} ghi nhận AQI trung bình cao nhất (<b>{peak_val:.1f}</b>); "
            f"tháng {low_month} có mức thấp nhất (<b>{low_val:.1f}</b>) — "
            f"biên độ dao động mùa vụ là <b>{peak_val - low_val:.1f}</b> đơn vị."
        )
        lines.append(
            "- Đỉnh ô nhiễm vào mùa đông thường được liên hệ với hiện tượng đốt rơm rạ sau thu hoạch "
            "và nghịch nhiệt nhiệt độ, tuy nhiên cần dữ liệu bổ sung để xác nhận nguyên nhân chính xác."
        )

    if not lines:
        return
    q = "Có xuất hiện tính mùa vụ trong ô nhiễm không khí hay không?"
    items = "".join(f"<li>{ln.lstrip('- ')}</li>" for ln in lines)
    with st.expander("Q2: Tính mùa vụ trong ô nhiễm không khí"):
        st.markdown(
            f"<h3>Câu hỏi</h3>"
            f"<p style='font-size:18px;'>{q}</p>"
            f"<h3>Trả lời</h3>"
            f"<ul style='font-size:18px;'>{items}</ul>",
            unsafe_allow_html=True,
        )


def _render_qa_cities(slopes: "pd.DataFrame") -> None:
    """Q&A block for Question 3 — placed below the city trend ranking chart."""
    if slopes.empty:
        return

    n_improving = int((slopes["trend_label"] == "Improving").sum())
    n_worsening = int((slopes["trend_label"] == "Worsening").sum())
    n_stable = int((slopes["trend_label"] == "Stable").sum())
    best_city_row = slopes.iloc[0]
    worst_city_row = slopes.iloc[-1]
    best_city = str(best_city_row["City"])
    best_slope = float(best_city_row["slope"])
    worst_city = str(worst_city_row["City"])
    worst_slope = float(worst_city_row["slope"])

    best_r2 = float(best_city_row["r_squared"])
    worst_r2 = float(worst_city_row["r_squared"])
    lines = [
        f"- Trong số các thành phố được phân tích, <b>{n_improving}</b> thành phố đang cải thiện, "
        f"<b>{n_worsening}</b> đang xấu đi và <b>{n_stable}</b> duy trì ổn định.",
        f"- Thành phố cải thiện mạnh nhất là {best_city} "
        f"(hệ số xu hướng: <b>{best_slope:+.2f}</b> AQI/tháng, R²=<b>{best_r2:.2f}</b>).",
        f"- Thành phố xấu đi nhiều nhất là {worst_city} "
        f"(hệ số xu hướng: <b>{worst_slope:+.2f}</b> AQI/tháng, R²=<b>{worst_r2:.2f}</b>) — "
        f"cần được ưu tiên trong các chính sách kiểm soát ô nhiễm.",
    ]
    q = "Thành phố nào đang cải thiện chất lượng không khí và thành phố nào đang trở nên ô nhiễm hơn theo thời gian?"
    items = "".join(f"<li>{ln.lstrip('- ')}</li>" for ln in lines)
    with st.expander("Q3: Thành phố nào cải thiện, thành phố nào xấu đi?"):
        st.markdown(
            f"<h3>Câu hỏi</h3>"
            f"<p style='font-size:18px;'>{q}</p>"
            f"<h3>Trả lời</h3>"
            f"<ul style='font-size:18px;'>{items}</ul>",
            unsafe_allow_html=True,
        )


def render() -> None:
    page_header(
        "Temporal Analysis",
        "AQI over months/years, seasonality, and city trend comparison.",
    )
    render_what_why_how()
    raw = get_city_day()
    filters = render_filter_state(raw, key_prefix="te_", show_pollutants=False, show_buckets=True)
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    section("Xu hướng AQI (2015–2020)")
    yearly = yearly_aqi_mean(df)
    monthly = monthly_aqi_mean(df)
    col_annual, col_monthly = st.columns(2)
    with col_annual:
        show_chart(yearly_aqi_line(yearly))
    with col_monthly:
        show_chart(monthly_aqi_line(monthly))

    section("Xu hướng AQI theo tháng — nhiều thành phố")
    city_monthly = monthly_aqi_by_city(df)
    if not city_monthly.empty:
        top6 = (
            city_monthly.groupby("City")["aqi_mean"]
            .mean()
            .nlargest(6)
            .index
        )
        city_monthly = city_monthly[city_monthly["City"].isin(top6)]
        st.caption("Hiển thị top 6 thành phố theo AQI trung bình. Dùng bộ lọc Thành phố để so sánh thành phố cụ thể.")
    show_chart(city_small_multiples_line(city_monthly))
    _render_qa_trend(yearly, monthly)

    section("Phân tích tính mùa vụ")
    wvn = winter_vs_nonwinter(df)
    if not wvn.empty:
        winter_row = wvn[wvn["season"].str.startswith("Winter")]
        nonwinter_row = wvn[~wvn["season"].str.startswith("Winter")]
        w_mean = float(winter_row["aqi_mean"].iloc[0]) if not winter_row.empty else None
        nw_mean = float(nonwinter_row["aqi_mean"].iloc[0]) if not nonwinter_row.empty else None
        kpi_left, kpi_right = st.columns(2)
        kpi_left.metric(
            "AQI trung bình mùa đông (Tháng 11–2)",
            f"{w_mean:.1f}" if w_mean is not None else "—",
            delta=f"{w_mean - nw_mean:+.1f} so với ngoài mùa đông" if (w_mean and nw_mean) else None,
            delta_color="inverse",
        )
        kpi_right.metric(
            "AQI trung bình ngoài mùa đông",
            f"{nw_mean:.1f}" if nw_mean is not None else "—",
        )
    profile = seasonal_monthly_profile(df)
    show_chart(seasonal_profile_bar(profile))
    _render_qa_seasonality(wvn, profile)

    section("Xếp hạng xu hướng theo thành phố (cải thiện vs xấu đi)")
    slopes = city_trend_slopes(df)
    if slopes.empty:
        st.info("Không đủ dữ liệu tháng để tính xu hướng thành phố. Hãy mở rộng khoảng thời gian.")
    else:
        show_chart(city_trend_slope_bar(slopes))
        improving = slopes[slopes["trend_label"] == "Improving"].head(10)
        worsening = slopes[slopes["trend_label"] == "Worsening"].sort_values("slope", ascending=False).head(10)
        tbl_left, tbl_right = st.columns(2)
        with tbl_left:
            st.caption("Top thành phố cải thiện")
            if not improving.empty:
                st.dataframe(
                    improving[["City", "slope", "r_squared", "n_months"]].rename(
                        columns={"slope": "AQI/tháng", "r_squared": "R²", "n_months": "Số tháng"}
                    ),
                    hide_index=True,
                )
            else:
                st.write("Không có thành phố nào trong bộ lọc hiện tại.")
        with tbl_right:
            st.caption("Top thành phố xấu đi")
            if not worsening.empty:
                st.dataframe(
                    worsening[["City", "slope", "r_squared", "n_months"]].rename(
                        columns={"slope": "AQI/tháng", "r_squared": "R²", "n_months": "Số tháng"}
                    ),
                    hide_index=True,
                )
            else:
                st.write("Không có thành phố nào trong bộ lọc hiện tại.")
        st.caption(
            "Hệ số xu hướng được tính bằng hồi quy tuyến tính (numpy polyfit). "
            "Các thành phố có ít hơn 12 tháng dữ liệu bị loại trừ. "
            "R² thấp cho thấy xu hướng nhiễu hoặc phi tuyến."
        )
        _render_qa_cities(slopes)
        st.download_button(
            "Tải dữ liệu xu hướng (CSV)",
            data=slopes.to_csv(index=False),
            file_name="city_trend_slopes.csv",
            mime="text/csv",
        )

    section("Số ngày AQI vượt ngưỡng theo năm")
    breach_df = aqi_breach_count_by_year(df, threshold=200)
    show_chart(aqi_breach_bar(breach_df, threshold=200))
