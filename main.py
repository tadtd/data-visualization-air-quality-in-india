"""Streamlit entrypoint: Air Quality in India dashboard."""

from __future__ import annotations

import streamlit as st

from dashboard.config import APP_ICON, APP_TITLE
from dashboard.router import run


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    run()


if __name__ == "__main__":
    main()
