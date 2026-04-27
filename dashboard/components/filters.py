"""Reusable sidebar filters producing FilterState."""

from __future__ import annotations

from datetime import date

import streamlit as st

from dashboard.data.schema import FilterState
from dashboard.data.transforms import default_date_range_from_df, list_cities


def render_filter_state(
    df,
    *,
    key_prefix: str = "",
) -> FilterState:
    """
    Render date range and city multiselect.
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

    return FilterState(
        date_start=date_start,
        date_end=date_end,
        cities=city_sel,
    )
