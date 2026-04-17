"""Shared Streamlit layout helpers: header, sidebar shell, sections."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from dashboard.config import APP_TITLE

if TYPE_CHECKING:
    from dashboard.data.schema import FilterState


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def app_sidebar_title() -> None:
    st.sidebar.title(APP_TITLE)
    st.sidebar.toggle(
        "♿ Chế độ mù màu",
        value=False,
        key="colorblind_mode",
        help="Bật chế độ bảng màu thân thiện với người mù màu (Okabe-Ito)",
    )
    st.sidebar.markdown("---")


def section(title: str, *, expanded: bool = True) -> None:
    """Visual separator for page sections."""
    st.markdown("---")
    st.subheader(title)


def render_filter_summary(filters: "FilterState") -> None:
    """Compact summary of active filters (debug / clarity)."""
    with st.expander("Bộ lọc đang áp dụng", expanded=False):
        st.json(
            {
                "khoảng_thời_gian": [str(filters.date_start), str(filters.date_end)],
                "thành_phố": filters.cities,
                "chất_ô_nhiễm": filters.pollutants,
                "mức_aqi": filters.aqi_buckets,
            }
        )
