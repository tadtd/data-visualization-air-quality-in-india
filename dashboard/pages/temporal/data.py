"""Temporal page data access and aggregations."""

from __future__ import annotations

import calendar

import numpy as np
import pandas as pd

from dashboard.config import MIN_TREND_MONTHS, TREND_LABELS, TREND_STABLE_THRESHOLD, WINTER_MONTHS
from dashboard.data.repositories import DatasetRepository
from dashboard.data.schema import COL_AQI, COL_CITY, COL_DATE


class TemporalData(DatasetRepository):
    """Temporal aggregates for AQI trend, seasonality, and city comparison."""

    dataset_kind = "city_day"

    @staticmethod
    def yearly_aqi_mean(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
            return pd.DataFrame()
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE])
        t["year"] = t[COL_DATE].dt.year
        grouped = (
            t.groupby("year", as_index=False)[COL_AQI]
            .agg(aqi_mean="mean", aqi_median="median", aqi_std="std")
        )
        return grouped

    @staticmethod
    def monthly_aqi_mean(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
            return pd.DataFrame()
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE])
        t["year_month"] = t[COL_DATE].dt.to_period("M").astype(str)
        grouped = t.groupby("year_month", as_index=False)[COL_AQI].mean()
        return grouped.rename(columns={COL_AQI: "aqi_mean"})

    @staticmethod
    def monthly_aqi_by_city(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns or COL_CITY not in df.columns:
            return pd.DataFrame()
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE, COL_CITY])
        t["year_month"] = t[COL_DATE].dt.to_period("M").astype(str)
        grouped = t.groupby(["year_month", COL_CITY], as_index=False)[COL_AQI].mean()
        return grouped.rename(columns={COL_AQI: "aqi_mean"})

    @staticmethod
    def winter_vs_nonwinter(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
            return pd.DataFrame()
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE])
        t["is_winter"] = t[COL_DATE].dt.month.isin(WINTER_MONTHS)
        grouped = (
            t.groupby("is_winter", as_index=False)[COL_AQI]
            .agg(aqi_mean="mean", aqi_std="std", n_days="count")
        )
        grouped["season"] = grouped["is_winter"].map({True: "Winter (Nov–Feb)", False: "Non-Winter"})
        return grouped[["season", "aqi_mean", "aqi_std", "n_days"]]

    @staticmethod
    def seasonal_monthly_profile(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
            return pd.DataFrame()
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE])
        t["month"] = t[COL_DATE].dt.month
        grouped = (
            t.groupby("month", as_index=False)[COL_AQI]
            .agg(aqi_mean="mean", aqi_std="std")
        )
        grouped["month_name"] = grouped["month"].apply(lambda month: calendar.month_abbr[month])
        grouped["is_winter"] = grouped["month"].isin(WINTER_MONTHS)
        return grouped.sort_values("month").reset_index(drop=True)

    @staticmethod
    def city_trend_slopes(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns or COL_CITY not in df.columns:
            return pd.DataFrame()
        monthly = TemporalData.monthly_aqi_by_city(df)
        if monthly.empty:
            return pd.DataFrame()

        monthly["_period"] = pd.to_datetime(monthly["year_month"] + "-01", errors="coerce")
        monthly = monthly.dropna(subset=["_period"])
        base = monthly["_period"].min()
        monthly["_t"] = ((monthly["_period"].dt.year - base.year) * 12) + (
            monthly["_period"].dt.month - base.month
        )

        records = []
        for city, group in monthly.groupby(COL_CITY):
            group = group.dropna(subset=["aqi_mean"]).sort_values("_t")
            n_months = len(group)
            if n_months < MIN_TREND_MONTHS:
                continue

            t_arr = group["_t"].to_numpy(dtype=float)
            y_arr = group["aqi_mean"].to_numpy(dtype=float)
            coeffs = np.polyfit(t_arr, y_arr, 1)
            slope = float(coeffs[0])
            predicted = np.polyval(coeffs, t_arr)
            ss_res = float(np.sum((y_arr - predicted) ** 2))
            ss_tot = float(np.sum((y_arr - y_arr.mean()) ** 2))
            r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

            if slope < -TREND_STABLE_THRESHOLD:
                label = TREND_LABELS["improving"]
            elif slope > TREND_STABLE_THRESHOLD:
                label = TREND_LABELS["worsening"]
            else:
                label = TREND_LABELS["stable"]

            records.append(
                {
                    COL_CITY: city,
                    "slope": slope,
                    "r_squared": r_squared,
                    "trend_label": label,
                    "n_months": n_months,
                }
            )

        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records).sort_values("slope").reset_index(drop=True)

    @staticmethod
    def year_on_year_monthly(df: pd.DataFrame) -> pd.DataFrame:
        """Monthly mean AQI with year and month columns for overlay comparison."""
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
            return pd.DataFrame()
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE])
        t["year"] = t[COL_DATE].dt.year
        t["month"] = t[COL_DATE].dt.month
        grouped = t.groupby(["year", "month"], as_index=False)[COL_AQI].mean()
        grouped = grouped.rename(columns={COL_AQI: "aqi_mean"})
        grouped["month_name"] = grouped["month"].apply(lambda m: calendar.month_abbr[m])
        return grouped.sort_values(["year", "month"])

    @staticmethod
    def aqi_breach_count_by_year(df: pd.DataFrame, *, threshold: int = 200) -> pd.DataFrame:
        if df.empty or COL_DATE not in df.columns or COL_AQI not in df.columns:
            return pd.DataFrame()
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE])
        t["year"] = t[COL_DATE].dt.year
        t["_breach"] = pd.to_numeric(t[COL_AQI], errors="coerce") > threshold
        grouped = t.groupby("year", as_index=False)["_breach"].sum().rename(columns={"_breach": "breach_days"})
        grouped["breach_days"] = grouped["breach_days"].astype(int)
        return grouped
