"""Reusable sidebar filters producing FilterState."""

from __future__ import annotations

from datetime import date

import streamlit as st

from dashboard.config import AQI_BUCKET_ORDER, AQI_BUCKET_VI
from dashboard.data.schema import FilterState
from dashboard.data.transforms import default_date_range_from_df, list_cities


def render_filter_state(
    df,
    *,
    key_prefix: str = "",
    show_buckets: bool = True,
) -> FilterState:
    """
    Render date range, city multiselect, and optional AQI buckets.
    `df` is expected to be city_day-like (City, Date, AQI_Bucket).
    """
    d0, d1 = default_date_range_from_df(df)
    cities_all = list_cities(df)

    r = st.sidebar.date_input(
        "Khoảng thời gian",
        value=(d0, d1),
        min_value=date(2000, 1, 1),
        max_value=date(2030, 12, 31),
        key=f"{key_prefix}date_range",
    )
    if isinstance(r, tuple) and len(r) == 2:
        date_start, date_end = r[0], r[1]
    else:
        date_start, date_end = d0, d1

    city_sel = st.sidebar.multiselect(
        "Thành phố (để trống = tất cả)",
        options=cities_all,
        default=[],
        key=f"{key_prefix}cities",
    )

    buckets: list[str] = []
    if show_buckets and df is not None and not df.empty and "AQI_Bucket" in df.columns:
        present = [b for b in AQI_BUCKET_ORDER if b in set(df["AQI_Bucket"].dropna().astype(str))]
        # Show Vietnamese labels but keep English values internally
        bucket_labels = {b: f"{AQI_BUCKET_VI.get(b, b)} ({b})" for b in present}
        buckets = st.sidebar.multiselect(
            "Mức AQI (để trống = tất cả)",
            options=present,
            default=[],
            format_func=lambda b: bucket_labels.get(b, b),
            key=f"{key_prefix}buckets",
        )

    return FilterState(
        date_start=date_start,
        date_end=date_end,
        cities=city_sel,
        aqi_buckets=buckets,
    )
