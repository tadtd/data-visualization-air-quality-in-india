"""Feature correlation analysis for AQI and pollutant drivers."""

from __future__ import annotations

from datetime import date
from typing import Literal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.data.schema import COL_AQI, COL_AQI_BUCKET, COL_CITY, COL_DATE
from dashboard.layout import page_header
from dashboard.pages._context import get_city_day

FEATURE_COLUMNS: list[str] = ["PM2.5", "PM10", "NO2", "SO2", "CO", COL_AQI]
POLLUTANT_COLUMNS: list[str] = [col for col in FEATURE_COLUMNS if col != COL_AQI]
ALL_CITIES = "All cities"
SEVERE_BUCKET = "Severe"
PARTICULATE_COLUMNS: tuple[str, str] = ("PM2.5", "PM10")
GAS_COLUMNS: tuple[str, str, str] = ("NO2", "SO2", "CO")

MissingStrategy = Literal[
    "Drop rows with missing feature values",
    "Fill missing feature values with median",
]


def validate_required_columns(df: pd.DataFrame) -> list[str]:
    """Return required columns that are missing from the loaded dataset."""
    required = [COL_CITY, COL_DATE, COL_AQI_BUCKET, *FEATURE_COLUMNS]
    return [col for col in required if col not in df.columns]


def prepare_base_data(df: pd.DataFrame) -> pd.DataFrame:
    """Keep relevant fields and coerce dates/features into analysis-ready types."""
    use_cols = [COL_CITY, COL_DATE, COL_AQI_BUCKET, *FEATURE_COLUMNS]
    prepared = df[use_cols].copy()

    prepared[COL_CITY] = prepared[COL_CITY].astype("string")
    prepared[COL_AQI_BUCKET] = prepared[COL_AQI_BUCKET].astype("string")
    prepared[COL_DATE] = pd.to_datetime(prepared[COL_DATE], errors="coerce")

    for col in FEATURE_COLUMNS:
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce")

    # Rows without City or Date cannot be used by the requested filters.
    return prepared.dropna(subset=[COL_CITY, COL_DATE])


def date_bounds(df: pd.DataFrame) -> tuple[date, date]:
    """Infer the available date range for the Streamlit slider."""
    if df.empty or COL_DATE not in df.columns:
        return date(2015, 1, 1), date(2020, 12, 31)

    dates = pd.to_datetime(df[COL_DATE], errors="coerce").dropna()
    if dates.empty:
        return date(2015, 1, 1), date(2020, 12, 31)

    return dates.min().date(), dates.max().date()


def render_sidebar_filters(
    df: pd.DataFrame,
) -> tuple[str, tuple[date, date], str, MissingStrategy]:
    """Render city, date, pollutant, and missing-value controls."""
    st.sidebar.markdown("### Feature Correlation Filters")

    city_options = [ALL_CITIES]
    if COL_CITY in df.columns:
        city_options += sorted(df[COL_CITY].dropna().astype(str).unique().tolist())

    selected_city = st.sidebar.selectbox(
        "City",
        options=city_options,
        key="correlation_city",
    )

    min_date, max_date = date_bounds(df)
    selected_dates = st.sidebar.slider(
        "Date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
        key="correlation_date_range",
    )

    selected_pollutant = st.sidebar.selectbox(
        "Pollutant for scatter plot",
        options=POLLUTANT_COLUMNS,
        key="correlation_pollutant",
    )

    missing_strategy = st.sidebar.radio(
        "Missing values",
        options=[
            "Drop rows with missing feature values",
            "Fill missing feature values with median",
        ],
        key="correlation_missing_strategy",
    )

    return selected_city, selected_dates, selected_pollutant, missing_strategy


def filter_data(
    df: pd.DataFrame,
    selected_city: str,
    selected_dates: tuple[date, date],
) -> pd.DataFrame:
    """Apply sidebar city and date filters."""
    if df.empty:
        return df.copy()

    start_date, end_date = selected_dates
    row_dates = pd.to_datetime(df[COL_DATE], errors="coerce").dt.date
    mask = (row_dates >= start_date) & (row_dates <= end_date)

    if selected_city != ALL_CITIES:
        mask &= df[COL_CITY].astype(str).eq(selected_city)

    return df.loc[mask].copy()


def handle_missing_values(df: pd.DataFrame, strategy: MissingStrategy) -> pd.DataFrame:
    """Drop or fill missing feature values before correlation and scatter analysis."""
    if df.empty:
        return df.copy()

    cleaned = df.copy()
    if strategy == "Fill missing feature values with median":
        medians = cleaned[FEATURE_COLUMNS].median(numeric_only=True)
        cleaned[FEATURE_COLUMNS] = cleaned[FEATURE_COLUMNS].fillna(medians)

    return cleaned.dropna(subset=FEATURE_COLUMNS)


def compute_pearson_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Pearson correlation for the requested pollutant and AQI features."""
    if df.empty:
        return pd.DataFrame(index=FEATURE_COLUMNS, columns=FEATURE_COLUMNS)
    return df[FEATURE_COLUMNS].corr(method="pearson")


def empty_figure(title: str, message: str) -> go.Figure:
    """Create a lightweight Plotly figure for empty filtered states."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
    )
    fig.update_layout(
        title=title,
        height=520,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def build_correlation_heatmap(correlation: pd.DataFrame) -> go.Figure:
    """Build an interactive heatmap where color encodes Pearson r strength."""
    if correlation.empty or correlation.isna().all().all():
        return empty_figure(
            "Pearson Correlation Heatmap",
            "No complete rows are available for correlation.",
        )

    fig = px.imshow(
        correlation,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
        labels=dict(color="Pearson r"),
    )
    fig.update_layout(
        title="Pearson Correlation Heatmap",
        height=520,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.update_xaxes(side="bottom")
    return fig


def build_aqi_scatter(df: pd.DataFrame, selected_pollutant: str) -> go.Figure:
    """Build an interactive scatter plot for a selected pollutant against AQI."""
    if df.empty:
        return empty_figure(
            f"{selected_pollutant} vs AQI",
            "No rows are available for the selected filters.",
        )

    fig = px.scatter(
        df,
        x=selected_pollutant,
        y=COL_AQI,
        color=COL_CITY,
        hover_data={
            COL_CITY: True,
            COL_DATE: "|%Y-%m-%d",
            selected_pollutant: ":.2f",
            COL_AQI: ":.2f",
        },
        opacity=0.65,
        render_mode="webgl",
    )
    fig.update_traces(marker=dict(size=6))
    fig.update_layout(
        title=f"{selected_pollutant} vs AQI",
        xaxis_title=selected_pollutant,
        yaxis_title="AQI",
        height=520,
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="City",
    )
    return fig


def compute_severe_pollutant_means(df: pd.DataFrame) -> pd.DataFrame:
    """Return mean pollutant levels for rows classified as Severe."""
    if df.empty or COL_AQI_BUCKET not in df.columns:
        return pd.DataFrame(columns=["Pollutant", "Mean Value"])

    severe_df = df[df[COL_AQI_BUCKET].astype(str).eq(SEVERE_BUCKET)]
    if severe_df.empty:
        return pd.DataFrame(columns=["Pollutant", "Mean Value"])

    means = (
        severe_df[POLLUTANT_COLUMNS]
        .apply(pd.to_numeric, errors="coerce")
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )
    return means.rename_axis("Pollutant").reset_index(name="Mean Value")


def extract_aqi_correlations(correlation: pd.DataFrame) -> pd.Series:
    """Return pollutant-to-AQI Pearson correlations sorted descending."""
    if correlation.empty or COL_AQI not in correlation.columns:
        return pd.Series(dtype="float64")

    aqi_corr = pd.to_numeric(correlation[COL_AQI], errors="coerce")
    aqi_corr = aqi_corr.reindex(POLLUTANT_COLUMNS).dropna()
    return aqi_corr.sort_values(ascending=False)


def mean_for_columns(series: pd.Series, columns: tuple[str, ...]) -> float | None:
    """Compute mean for selected columns, returning None when unavailable."""
    if series.empty:
        return None

    values = pd.to_numeric(series.reindex(columns), errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.mean())


def sum_for_columns(series: pd.Series, columns: tuple[str, ...]) -> float | None:
    """Compute sum for selected columns, returning None when unavailable."""
    if series.empty:
        return None

    values = pd.to_numeric(series.reindex(columns), errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.sum())


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    """Return ratio while guarding against missing or zero denominator values."""
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator / denominator)


def fmt(value: float | None, precision: int = 2) -> str:
    """Format optional float with a fixed precision for readable insight text."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.{precision}f}"


def render_vietnamese_insights(
    correlation: pd.DataFrame,
    severe_means: pd.DataFrame,
) -> None:
    """Render concise Vietnamese insights from correlation and Severe means."""
    st.markdown("---")
    st.subheader("Insights dành cho nhà hoạch định chính sách")

    aqi_corr = extract_aqi_correlations(correlation)
    if severe_means.empty:
        severe_series = pd.Series(dtype="float64")
    else:
        severe_series = severe_means.set_index("Pollutant")["Mean Value"]

    if aqi_corr.empty and severe_series.empty:
        st.info("Chưa đủ dữ liệu để tạo insight cho bộ lọc hiện tại.")
        return

    strongest_pollutant = str(aqi_corr.index[0]) if not aqi_corr.empty else "N/A"
    strongest_r = float(aqi_corr.iloc[0]) if not aqi_corr.empty else None

    pm_corr_mean = mean_for_columns(aqi_corr, PARTICULATE_COLUMNS)
    gas_corr_mean = mean_for_columns(aqi_corr, GAS_COLUMNS)
    pm_vs_gas_corr_ratio = safe_ratio(pm_corr_mean, gas_corr_mean)

    dominant_pollutant = str(severe_series.sort_values(ascending=False).index[0]) if not severe_series.empty else "N/A"
    dominant_value = float(severe_series.sort_values(ascending=False).iloc[0]) if not severe_series.empty else None

    pm_severe_total = sum_for_columns(severe_series, PARTICULATE_COLUMNS)
    gas_severe_total = sum_for_columns(severe_series, GAS_COLUMNS)
    pm_vs_gas_severe_ratio = safe_ratio(pm_severe_total, gas_severe_total)

    policy_recommendation = (
        "Ưu tiên ngân sách ngắn hạn cho kiểm soát bụi (PM10/PM2.5): kiểm soát bụi đường, công trình và xe tải nặng; "
        "kích hoạt kịch bản ứng phó theo ngưỡng Severe tại điểm nóng đô thị."
        if (strongest_pollutant in PARTICULATE_COLUMNS)
        else "Tăng cường kiểm soát nguồn khí chi phối (đặc biệt NO2/SO2/CO) kết hợp cảnh báo sớm theo ngưỡng Severe."
    )

    with st.expander("Tóm tắt phân tích cho nhà hoạch định", expanded=True):
        st.markdown(
            f"""
1. **Chất ảnh hưởng AQI mạnh nhất:** {strongest_pollutant} với hệ số tương quan Pearson **r = {fmt(strongest_r, 3)}**.

2. **So sánh bụi hạt và khí:** tương quan trung bình nhóm PM là **{fmt(pm_corr_mean, 3)}**, nhóm khí là **{fmt(gas_corr_mean, 3)}**; PM cao hơn khoảng **{fmt(pm_vs_gas_corr_ratio, 2)} lần**.

3. **Chất trội trong điều kiện Severe:** {dominant_pollutant} với giá trị trung bình **{fmt(dominant_value, 2)}**. Tổng PM trên ngày Severe cao khoảng **{fmt(pm_vs_gas_severe_ratio, 2)} lần** tổng nhóm khí.

4. **Khuyến nghị hành động:** {policy_recommendation}
            """
        )


def build_severe_contributors_bar(mean_df: pd.DataFrame) -> go.Figure:
    """Build a descending bar chart for Severe AQI pollutant contributors."""
    if mean_df.empty:
        return empty_figure(
            "Mean Pollutant Levels on Severe AQI Days",
            "No Severe AQI rows are available for the selected filters.",
        )

    fig = px.bar(
        mean_df,
        x="Pollutant",
        y="Mean Value",
        text="Mean Value",
        color="Pollutant",
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        title="Mean Pollutant Levels on Severe AQI Days",
        xaxis_title="Pollutant",
        yaxis_title="Mean Value",
        height=440,
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=False,
    )
    return fig


def build_bucket_distribution_boxplot(df: pd.DataFrame) -> go.Figure:
    """Build a pollutant distribution boxplot grouped by AQI bucket."""
    if df.empty or COL_AQI_BUCKET not in df.columns:
        return empty_figure(
            "Pollutant Distribution Across AQI Buckets",
            "No AQI bucket data is available for the selected filters.",
        )

    long_df = df[[COL_AQI_BUCKET, *POLLUTANT_COLUMNS]].melt(
        id_vars=COL_AQI_BUCKET,
        value_vars=POLLUTANT_COLUMNS,
        var_name="Pollutant",
        value_name="Value",
    )
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    long_df = long_df.dropna(subset=[COL_AQI_BUCKET, "Value"])

    if long_df.empty:
        return empty_figure(
            "Pollutant Distribution Across AQI Buckets",
            "No pollutant values are available for the selected filters.",
        )

    fig = px.box(
        long_df,
        x="Pollutant",
        y="Value",
        color=COL_AQI_BUCKET,
        points=False,
    )
    fig.update_layout(
        title="Pollutant Distribution Across AQI Buckets",
        xaxis_title="Pollutant",
        yaxis_title="Value",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="AQI Bucket",
    )
    return fig


def render_severe_pollution_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Render Severe AQI contributor analysis and return Severe mean values."""
    st.markdown("---")
    st.subheader("Severe Pollution Contributors")

    severe_means = compute_severe_pollutant_means(df)
    severe_rows = int(df[COL_AQI_BUCKET].astype(str).eq(SEVERE_BUCKET).sum())

    if severe_means.empty:
        st.info("No Severe AQI rows are available for the selected filters.")
        st.plotly_chart(build_severe_contributors_bar(severe_means), width="stretch")
    else:
        top_row = severe_means.iloc[0]
        st.metric(
            "Top contributing pollutant",
            str(top_row["Pollutant"]),
            f"Mean value: {top_row['Mean Value']:.2f}",
        )
        st.caption(f"Severe AQI rows in current filters: {severe_rows}")
        st.plotly_chart(build_severe_contributors_bar(severe_means), width="stretch")

    if st.checkbox(
        "Show pollutant distribution across AQI buckets",
        key="correlation_show_bucket_boxplot",
    ):
        st.plotly_chart(build_bucket_distribution_boxplot(df), width="stretch")

    return severe_means


def render_what_why_how() -> None:
    """Add the analysis framing requested for the module."""
    with st.expander("What, Why, How", expanded=True):
        st.markdown(
            """
**What:** Compare PM2.5, PM10, NO2, SO2, CO, and AQI to measure how air quality features move together.

**Why:** Strong positive relationships with AQI help identify pollutant features that may explain high-risk air quality days.

**How:** Filter by city and date, clean missing feature values, compute Pearson correlation, then inspect pollutant-to-AQI patterns in the scatter plot.
            """
        )


def render_filter_summary(
    selected_city: str,
    selected_dates: tuple[date, date],
    selected_pollutant: str,
    missing_strategy: MissingStrategy,
    filtered_rows: int,
    analysis_rows: int,
) -> None:
    """Show compact data-processing context for reproducibility."""
    with st.expander("Active analysis settings", expanded=False):
        st.json(
            {
                "city": selected_city,
                "date_range": [str(selected_dates[0]), str(selected_dates[1])],
                "scatter_pollutant": selected_pollutant,
                "missing_value_strategy": missing_strategy,
                "rows_after_filters": filtered_rows,
                "rows_after_missing_value_handling": analysis_rows,
                "correlation_features": FEATURE_COLUMNS,
            }
        )


def render() -> None:
    """Render the Feature Correlation page."""
    page_header(
        "Feature Correlation Analysis",
        "Pearson relationships between selected pollutant features and AQI.",
    )
    render_what_why_how()

    raw = get_city_day()
    if raw.empty:
        st.warning("city_day.csv is missing or empty.")
        return

    missing_columns = validate_required_columns(raw)
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return

    base_df = prepare_base_data(raw)
    selected_city, selected_dates, selected_pollutant, missing_strategy = (
        render_sidebar_filters(base_df)
    )

    filtered_df = filter_data(base_df, selected_city, selected_dates)
    analysis_df = handle_missing_values(filtered_df, missing_strategy)
    render_filter_summary(
        selected_city,
        selected_dates,
        selected_pollutant,
        missing_strategy,
        filtered_rows=len(filtered_df),
        analysis_rows=len(analysis_df),
    )

    if analysis_df.empty:
        st.warning("No complete rows remain after filtering and missing-value handling.")

    correlation = compute_pearson_correlation(analysis_df)

    heatmap_col, scatter_col = st.columns(2)
    with heatmap_col:
        st.plotly_chart(build_correlation_heatmap(correlation), width="stretch")

    with scatter_col:
        st.plotly_chart(
            build_aqi_scatter(analysis_df, selected_pollutant),
            width="stretch",
        )

    severe_means = render_severe_pollution_analysis(filtered_df)
    render_vietnamese_insights(correlation, severe_means)
