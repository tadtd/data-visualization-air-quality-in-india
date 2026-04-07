"""Aggregations and transforms for dashboard pages."""

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
    """Apply shared FilterState to a city_day-like frame."""
    if df.empty:
        return df
    m = _mask_date(df, filters) & _mask_city(df, filters) & _mask_bucket(df, filters)
    return df.loc[m].copy()


def kpi_summary(df: pd.DataFrame) -> dict[str, float | int]:
    """Simple KPIs when AQI column exists."""
    if df.empty or COL_AQI not in df.columns:
        return {"mean_aqi": float("nan"), "median_aqi": float("nan"), "rows": len(df)}
    s = pd.to_numeric(df[COL_AQI], errors="coerce")
    return {
        "mean_aqi": float(s.mean()),
        "median_aqi": float(s.median()),
        "rows": int(len(df)),
    }


def monthly_aqi_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly mean AQI by period."""
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE])
    t["year_month"] = t[COL_DATE].dt.to_period("M").astype(str)
    g = t.groupby("year_month", as_index=False)[COL_AQI].mean()
    return g.rename(columns={COL_AQI: "aqi_mean"})


def city_mean_aqi(df: pd.DataFrame) -> pd.DataFrame:
    """Mean AQI per city."""
    if df.empty or COL_CITY not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    g = (
        df.groupby(COL_CITY, as_index=False)[COL_AQI]
        .mean()
        .sort_values(COL_AQI, ascending=False)
    )
    return g.rename(columns={COL_AQI: "aqi_mean"})


def dangerous_day_counts_by_city(df: pd.DataFrame) -> pd.DataFrame:
    """Count days in Poor / Very Poor / Severe per city."""
    if df.empty or COL_CITY not in df.columns or COL_AQI_BUCKET not in df.columns:
        return pd.DataFrame()
    sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)]
    if sub.empty:
        return pd.DataFrame(columns=[COL_CITY, "danger_days"])
    g = sub.groupby(COL_CITY, as_index=False).size().rename(columns={"size": "danger_days"})
    return g.sort_values("danger_days", ascending=False)


def default_date_range_from_df(df: pd.DataFrame) -> tuple[date, date]:
    """Infer min/max date for filter defaults."""
    if df.empty or COL_DATE not in df.columns:
        return date(2015, 1, 1), date(2020, 12, 31)
    s = pd.to_datetime(df[COL_DATE], errors="coerce").dropna()
    if s.empty:
        return date(2015, 1, 1), date(2020, 12, 31)
    return s.min().date(), s.max().date()


def list_cities(df: pd.DataFrame) -> list[str]:
    if df.empty or COL_CITY not in df.columns:
        return []
    return sorted(df[COL_CITY].dropna().astype(str).unique().tolist())
