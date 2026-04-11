"""Top-level page routing for the hybrid Streamlit dashboard."""

from __future__ import annotations

import streamlit as st

from dashboard.config import PAGE_KEYS, PAGE_LABELS
from dashboard.layout import app_sidebar_title
from dashboard.pages import (
    city_ranking,
    correlation,
    danger_frequency,
    geography,
    insights,
    overview,
    temporal,
)


def _page_options() -> list[str]:
    return [PAGE_LABELS[k] for k in PAGE_KEYS]


def _key_from_label(label: str) -> str:
    for k, v in PAGE_LABELS.items():
        if v == label:
            return k
    return "overview"


def run() -> None:
    app_sidebar_title()
    st.sidebar.markdown("### Navigation")
    choice = st.sidebar.radio(
        "Page",
        options=_page_options(),
        label_visibility="collapsed",
    )
    page_key = _key_from_label(choice)

    if page_key == "overview":
        overview.render()
    elif page_key == "city_ranking":
        city_ranking.render()
    elif page_key == "danger_frequency":
        danger_frequency.render()
    elif page_key == "temporal":
        temporal.render()
    elif page_key == "geography":
        geography.render()
    elif page_key == "correlation":
        correlation.render()
    elif page_key == "insights":
        insights.render()
    else:
        overview.render()
