"""Top-level page routing using horizontal st.tabs."""

from __future__ import annotations

import streamlit as st

from dashboard.config import PAGE_KEYS, PAGE_LABELS
from dashboard.components.filters import render_filter_state
from dashboard.data.loader import data_status_message, load_dataset
from dashboard.layout import app_sidebar_title
from dashboard.pages import correlation, geography, insights, overview, temporal
from dashboard.theme import inject_theme

_TAB_LABELS = [PAGE_LABELS[k] for k in PAGE_KEYS]
_RENDERERS = [
    overview.render,
    geography.render,
    correlation.render,
    temporal.render,
    insights.render,
]


def run() -> None:
    inject_theme()
    app_sidebar_title()

    # Show data status once in sidebar
    msg = data_status_message()
    if msg:
        st.sidebar.caption(msg)

    # Shared filters rendered once in sidebar
    raw = load_dataset("city_day")
    if raw is None:
        raw_df = __import__("pandas").DataFrame()
    else:
        raw_df = raw

    filters = render_filter_state(
        raw_df, key_prefix="shared_", show_pollutants=True, show_buckets=True
    )

    # Store filters in session state for pages to read
    st.session_state["shared_filters"] = filters
    st.session_state["shared_raw_df"] = raw_df

    tabs = st.tabs(_TAB_LABELS)
    for tab, renderer in zip(tabs, _RENDERERS):
        with tab:
            renderer()
