"""Overview: KPIs + quick trend + city ranking snapshot."""

from __future__ import annotations

import math

from dashboard.components.charts import city_bar_top_bottom, monthly_aqi_line, show_chart
from dashboard.components.filters import render_filter_state
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data.transform import apply_filters, city_mean_aqi, kpi_summary, monthly_aqi_mean
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day


def render() -> None:
    page_header(
        "Overview",
        "High-level KPIs, monthly AQI snapshot, and city ranking preview.",
    )
    raw = get_city_day()
    filters = render_filter_state(raw, key_prefix="ov_", show_pollutants=False, show_buckets=True)
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    section("Key metrics")
    kpis = kpi_summary(df)
    mean_v = kpis["mean_aqi"]
    med_v = kpis["median_aqi"]
    mean_display = (
        "—"
        if kpis["rows"] == 0 or (isinstance(mean_v, float) and math.isnan(mean_v))
        else round(mean_v, 2)
    )
    med_display = (
        "—"
        if kpis["rows"] == 0 or (isinstance(med_v, float) and math.isnan(med_v))
        else round(med_v, 2)
    )
    render_kpi_row(
        {
            "Mean AQI": mean_display,
            "Median AQI": med_display,
            "Rows (filtered)": kpis["rows"],
        },
        columns=3,
    )

    section("Temporal snapshot")
    m = monthly_aqi_mean(df)
    show_chart(monthly_aqi_line(m))

    section("Geographic snapshot")
    c = city_mean_aqi(df)
    show_chart(city_bar_top_bottom(c, top_n=8))
