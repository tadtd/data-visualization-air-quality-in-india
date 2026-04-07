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


def section(title: str, *, expanded: bool = True) -> None:
    """Visual separator for page sections."""
    st.markdown("---")
    st.subheader(title)


def render_filter_summary(filters: "FilterState") -> None:
    """Compact summary of active filters (debug / clarity)."""
    with st.expander("Active filters", expanded=False):
        st.json(
            {
                "date_range": [str(filters.date_start), str(filters.date_end)],
                "cities": filters.cities,
                "pollutants": filters.pollutants,
                "aqi_buckets": filters.aqi_buckets,
            }
        )
