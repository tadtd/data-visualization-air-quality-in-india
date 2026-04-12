"""Cross-page filter and aggregation helpers for dashboard pages."""

from __future__ import annotations

from datetime import date

import pandas as pd

from dashboard.config import DANGEROUS_AQI_BUCKETS
from dashboard.data.schema import COL_AQI, COL_AQI_BUCKET, COL_CITY, COL_DATE, FilterState


def _mask_date(df: pd.DataFrame, filters: FilterState) -> pd.Series:
    if COL_DATE not in df.columns:
        return pd.Series(True, index=df.index)
    d = pd.to_datetime(df[COL_DATE]).dt.date
    return (d >= filters.date_start) & (d <= filters.date_end)


def _mask_city(df: pd.DataFrame, filters: FilterState) -> pd.Series:
    if not filters.cities or COL_CITY not in df.columns:
        return pd.Series(True, index=df.index)
    return df[COL_CITY].isin(filters.cities)


def _mask_bucket(df: pd.DataFrame, filters: FilterState) -> pd.Series:
    if not filters.aqi_buckets or COL_AQI_BUCKET not in df.columns:
        return pd.Series(True, index=df.index)
    return df[COL_AQI_BUCKET].isin(filters.aqi_buckets)


def apply_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    """Apply the shared filter model to a city-day-like frame."""
    if df.empty:
        return df
    mask = _mask_date(df, filters) & _mask_city(df, filters) & _mask_bucket(df, filters)
    return df.loc[mask].copy()


def summarize_aqi_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Return AQI KPIs used across pages."""
    if df.empty or COL_AQI not in df.columns:
        return {"mean_aqi": float("nan"), "median_aqi": float("nan"), "rows": len(df)}
    values = pd.to_numeric(df[COL_AQI], errors="coerce")
    return {
        "mean_aqi": float(values.mean()),
        "median_aqi": float(values.median()),
        "rows": int(len(df)),
    }


def mean_aqi_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly mean AQI by period."""
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE])
    t["year_month"] = t[COL_DATE].dt.to_period("M").astype(str)
    grouped = t.groupby("year_month", as_index=False)[COL_AQI].mean()
    return grouped.rename(columns={COL_AQI: "aqi_mean"})


def mean_aqi_by_city(df: pd.DataFrame) -> pd.DataFrame:
    """Mean AQI per city."""
    if df.empty or COL_CITY not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    grouped = (
        df.groupby(COL_CITY, as_index=False)[COL_AQI]
        .mean()
        .sort_values(COL_AQI, ascending=False)
    )
    return grouped.rename(columns={COL_AQI: "aqi_mean"})


def count_dangerous_days_by_city(df: pd.DataFrame) -> pd.DataFrame:
    """Count days in Poor / Very Poor / Severe per city."""
    if df.empty or COL_CITY not in df.columns or COL_AQI_BUCKET not in df.columns:
        return pd.DataFrame()
    subset = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)]
    if subset.empty:
        return pd.DataFrame(columns=[COL_CITY, "danger_days"])
    grouped = subset.groupby(COL_CITY, as_index=False).size().rename(columns={"size": "danger_days"})
    return grouped.sort_values("danger_days", ascending=False)


def dangerous_day_counts_by_city_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """Count dangerous days per city and per AQI bucket (Poor / Very Poor / Severe)."""
    if df.empty or COL_CITY not in df.columns or COL_AQI_BUCKET not in df.columns:
        return pd.DataFrame()
    subset = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)]
    if subset.empty:
        return pd.DataFrame(columns=[COL_CITY, COL_AQI_BUCKET, "days"])
    counts = subset.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False).size().rename(columns={"size": "days"})
    return counts


def default_date_range_from_df(df: pd.DataFrame) -> tuple[date, date]:
    """Infer min/max date for filter defaults."""
    if df.empty or COL_DATE not in df.columns:
        return date(2015, 1, 1), date(2020, 12, 31)
    series = pd.to_datetime(df[COL_DATE], errors="coerce").dropna()
    if series.empty:
        return date(2015, 1, 1), date(2020, 12, 31)
    return series.min().date(), series.max().date()


def list_cities(df: pd.DataFrame) -> list[str]:
    """Sorted list of available cities in a frame."""
    if df.empty or COL_CITY not in df.columns:
        return []
    return sorted(df[COL_CITY].dropna().astype(str).unique().tolist())


# ---------------------------------------------------------------------------
# State-level helpers (require stations.csv join)
# ---------------------------------------------------------------------------
COL_STATE = "State"


def city_to_state_map(stations_df: pd.DataFrame) -> dict[str, str]:
    """Build a city -> state mapping from the stations table."""
    if stations_df.empty or COL_CITY not in stations_df.columns or COL_STATE not in stations_df.columns:
        return {}
    mapping = (
        stations_df[[COL_CITY, COL_STATE]]
        .dropna()
        .drop_duplicates(subset=[COL_CITY])
        .set_index(COL_CITY)[COL_STATE]
        .to_dict()
    )
    return mapping


def merge_state_info(df: pd.DataFrame, stations_df: pd.DataFrame) -> pd.DataFrame:
    """Join the State column onto a city-day-like frame."""
    if df.empty:
        return df
    mapping = city_to_state_map(stations_df)
    if not mapping:
        return df
    out = df.copy()
    out[COL_STATE] = out[COL_CITY].map(mapping)
    return out


def mean_aqi_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Mean AQI per state (requires State column already merged)."""
    if df.empty or COL_STATE not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    grouped = (
        df.dropna(subset=[COL_STATE])
        .groupby(COL_STATE, as_index=False)[COL_AQI]
        .mean()
        .sort_values(COL_AQI, ascending=False)
    )
    return grouped.rename(columns={COL_AQI: "aqi_mean"})
