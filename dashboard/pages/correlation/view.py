"""Streamlit view for the Correlation page."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from dashboard.data.loader import data_status_message
from dashboard.pages.correlation.charts import CorrelationCharts
from dashboard.pages.correlation.data import (
    POLLUTANT_COLUMNS,
    CorrelationData,
    MissingStrategy,
    SEVERE_BUCKET,
)
from dashboard.theme import section_divider


def _render_sidebar_filters(
    df: pd.DataFrame,
) -> tuple[str, tuple[date, date], str, MissingStrategy]:
    st.sidebar.markdown("### Correlation Filters")
    city_options = ["All cities"]
    if "City" in df.columns:
        city_options += sorted(df["City"].dropna().astype(str).unique().tolist())

    selected_city = st.sidebar.selectbox("City", options=city_options, key="correlation_city")
    min_date, max_date = CorrelationData.date_bounds(df)
    selected_dates = st.sidebar.slider(
        "Date range",
        min_value=min_date, max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
        key="correlation_date_range",
    )
    selected_pollutant = st.sidebar.selectbox(
        "Pollutant for scatter plot",
        options=POLLUTANT_COLUMNS, key="correlation_pollutant",
    )
    missing_strategy: MissingStrategy = st.sidebar.radio(
        "Missing values",
        options=[
            "Drop rows with missing feature values",
            "Fill missing feature values with median",
        ],
        key="correlation_missing_strategy",
    )
    return selected_city, selected_dates, selected_pollutant, missing_strategy


def render() -> None:
    """Render the Correlation page."""
    st.sidebar.caption(data_status_message())
    raw = CorrelationData.load_frame()
    if raw.empty:
        st.warning("city_day.csv is missing or empty.")
        return

    missing_columns = CorrelationData.validate_required_columns(raw)
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return

    base_df = CorrelationData.prepare_base_data(raw)
    selected_city, selected_dates, selected_pollutant, missing_strategy = _render_sidebar_filters(base_df)
    filtered_df = CorrelationData.filter_data(base_df, selected_city, selected_dates)
    analysis_df = CorrelationData.handle_missing_values(filtered_df, missing_strategy)

    if analysis_df.empty:
        st.warning("No complete rows remain after filtering.")
        return

    # --- Heatmap + Scatter side by side ---
    correlation = CorrelationData.pearson_matrix(analysis_df)
    heatmap_col, scatter_col = st.columns(2)
    with heatmap_col:
        st.plotly_chart(CorrelationCharts.pearson_heatmap(correlation), width="stretch")
    with scatter_col:
        st.plotly_chart(CorrelationCharts.aqi_scatter(analysis_df, selected_pollutant), width="stretch")

    section_divider()

    # --- Severe contributors ---
    severe_means = CorrelationData.severe_pollutant_means(filtered_df)
    severe_rows = int(filtered_df["AQI_Bucket"].astype(str).eq(SEVERE_BUCKET).sum()) if "AQI_Bucket" in filtered_df.columns else 0

    if severe_means.empty:
        st.info("No Severe AQI rows for selected filters.")
    else:
        st.metric("Top Contributing Pollutant", str(severe_means.iloc[0]["Pollutant"]),
                   f"Mean: {severe_means.iloc[0]['Mean Value']:.1f} | Severe days: {severe_rows}")
    st.plotly_chart(CorrelationCharts.severe_contributors_bar(severe_means), width="stretch")

    section_divider()

    # --- Optional boxplot ---
    if st.checkbox("Show pollutant distribution across AQI buckets", key="correlation_show_bucket_boxplot"):
        st.plotly_chart(CorrelationCharts.bucket_boxplot(filtered_df), width="stretch")
