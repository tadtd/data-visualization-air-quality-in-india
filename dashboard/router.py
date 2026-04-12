"""Top-level page routing using horizontal st.tabs."""

from __future__ import annotations

import streamlit as st

from dashboard.config import PAGE_KEYS, PAGE_LABELS
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

    tabs = st.tabs(_TAB_LABELS)
    for tab, renderer in zip(tabs, _RENDERERS):
        with tab:
            renderer()
