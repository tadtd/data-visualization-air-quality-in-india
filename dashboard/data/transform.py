"""Aggregations and transforms for dashboard pages."""

from __future__ import annotations

from datetime import date

import pandas as pd

import calendar

import calendar

import numpy as np

from dashboard.config import DANGEROUS_AQI_BUCKETS, MIN_TREND_MONTHS, TREND_LABELS, TREND_STABLE_THRESHOLD, WINTER_MONTHS
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


def city_trend_slopes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Linear regression slope (AQI/month) per city over time.
    Cities with fewer than MIN_TREND_MONTHS data points are excluded.
    Returns: City, slope, r_squared, trend_label, n_months — sorted by slope ascending.
    """
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns or COL_CITY not in df.columns:
        return pd.DataFrame()

    monthly = monthly_aqi_by_city(df)
    if monthly.empty:
        return pd.DataFrame()

    # Encode year_month as an integer index for regression
    monthly["_period"] = pd.to_datetime(monthly["year_month"] + "-01", errors="coerce")
    monthly = monthly.dropna(subset=["_period"])
    base = monthly["_period"].min()
    monthly["_t"] = ((monthly["_period"].dt.year - base.year) * 12
                     + (monthly["_period"].dt.month - base.month))

    records = []
    for city, grp in monthly.groupby(COL_CITY):
        grp = grp.dropna(subset=["aqi_mean"]).sort_values("_t")
        n = len(grp)
        if n < MIN_TREND_MONTHS:
            continue
        t = grp["_t"].to_numpy(dtype=float)
        y = grp["aqi_mean"].to_numpy(dtype=float)
        coeffs = np.polyfit(t, y, 1)
        slope = float(coeffs[0])
        # R² from residuals
        y_pred = np.polyval(coeffs, t)
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

        if slope < -TREND_STABLE_THRESHOLD:
            label = TREND_LABELS["improving"]
        elif slope > TREND_STABLE_THRESHOLD:
            label = TREND_LABELS["worsening"]
        else:
            label = TREND_LABELS["stable"]

        records.append({
            COL_CITY: city,
            "slope": slope,
            "r_squared": r_squared,
            "trend_label": label,
            "n_months": n,
        })

    if not records:
        return pd.DataFrame()

    result = pd.DataFrame(records).sort_values("slope").reset_index(drop=True)
    return result


def seasonal_monthly_profile(df: pd.DataFrame) -> pd.DataFrame:
    """AQI aggregated by calendar month (1–12) across all years — reveals seasonality."""
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE])
    t["month"] = t[COL_DATE].dt.month
    g = (
        t.groupby("month", as_index=False)[COL_AQI]
        .agg(aqi_mean="mean", aqi_std="std")
    )
    g["month_name"] = g["month"].apply(lambda m: calendar.month_abbr[m])
    g["is_winter"] = g["month"].isin(WINTER_MONTHS)
    return g.sort_values("month").reset_index(drop=True)


def winter_vs_nonwinter(df: pd.DataFrame) -> pd.DataFrame:
    """Compare mean AQI for winter (Nov–Feb) vs non-winter months."""
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE])
    t["is_winter"] = t[COL_DATE].dt.month.isin(WINTER_MONTHS)
    g = (
        t.groupby("is_winter", as_index=False)[COL_AQI]
        .agg(aqi_mean="mean", aqi_std="std", n_days="count")
    )
    g["season"] = g["is_winter"].map({True: "Winter (Nov–Feb)", False: "Non-Winter"})
    return g[["season", "aqi_mean", "aqi_std", "n_days"]]


def monthly_aqi_by_city(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly mean AQI per city — for multi-city overlay trend chart."""
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns or COL_CITY not in df.columns:
        return pd.DataFrame()
    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE, COL_CITY])
    t["year_month"] = t[COL_DATE].dt.to_period("M").astype(str)
    g = t.groupby(["year_month", COL_CITY], as_index=False)[COL_AQI].mean()
    return g.rename(columns={COL_AQI: "aqi_mean"})


def yearly_aqi_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Annual mean, median, and std AQI — for year-over-year trend chart."""
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE])
    t["year"] = t[COL_DATE].dt.year
    g = (
        t.groupby("year", as_index=False)[COL_AQI]
        .agg(aqi_mean="mean", aqi_median="median", aqi_std="std")
    )
    return g


def aqi_breach_count_by_year(df: pd.DataFrame, *, threshold: int = 200) -> pd.DataFrame:
    """Count days per year where AQI exceeds the given threshold."""
    if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
        return pd.DataFrame()
    t = df.copy()
    t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
    t = t.dropna(subset=[COL_DATE])
    t["year"] = t[COL_DATE].dt.year
    t["_breach"] = pd.to_numeric(t[COL_AQI], errors="coerce") > threshold
    g = t.groupby("year", as_index=False)["_breach"].sum().rename(columns={"_breach": "breach_days"})
    g["breach_days"] = g["breach_days"].astype(int)
    return g
