"""Geographic comparison: top/bottom cities, dangerous-day frequency."""

from __future__ import annotations

from dashboard.components.charts import city_bar_top_bottom, dangerous_days_bar, show_chart
from dashboard.components.filters import render_filter_state
from dashboard.data.transform import apply_filters, city_mean_aqi, dangerous_day_counts_by_city
from dashboard.layout import page_header, render_filter_summary, section
from dashboard.pages._context import get_city_day


def render() -> None:
    page_header(
        "Geographic Comparison",
        "Best/worst cities by mean AQI and frequency of dangerous AQI buckets.",
    )
    raw = get_city_day()
    filters = render_filter_state(raw, key_prefix="geo_", show_pollutants=False, show_buckets=True)
    render_filter_summary(filters)
    df = apply_filters(raw, filters)

    section("Mean AQI by city (top / bottom)")
    c = city_mean_aqi(df)
    show_chart(city_bar_top_bottom(c, top_n=10))

    section("Dangerous days (Poor, Very Poor, Severe) by city")
    d = dangerous_day_counts_by_city(df)
    show_chart(dangerous_days_bar(d, top_n=15))
