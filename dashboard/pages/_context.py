"""Shared data context for Streamlit pages."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.data.loader import data_status_message, load_dataset


def get_city_day() -> pd.DataFrame:
    """Load city_day; empty frame if missing. Shows data path hint in sidebar."""
    st.sidebar.caption(data_status_message())
    df = load_dataset("city_day")
    return df if df is not None else pd.DataFrame()
