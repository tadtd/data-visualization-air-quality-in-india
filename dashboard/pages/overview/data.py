"""Overview page data access and shared summaries."""

from __future__ import annotations

import pandas as pd

from dashboard.config import CITY_COORDINATES
from dashboard.data.repositories import DatasetRepository
from dashboard.data.schema import COL_AQI, COL_AQI_BUCKET, COL_CITY
from dashboard.data.transforms import mean_aqi_by_city, mean_aqi_by_month, summarize_aqi_kpis


class OverviewData(DatasetRepository):
    """Data access and summaries for the Overview page."""

    dataset_kind = "city_day"

    @staticmethod
    def summarize_kpis(df: pd.DataFrame) -> dict[str, float | int]:
        return summarize_aqi_kpis(df)

    @staticmethod
    def monthly_mean(df: pd.DataFrame) -> pd.DataFrame:
        return mean_aqi_by_month(df)

    @staticmethod
    def city_mean(df: pd.DataFrame) -> pd.DataFrame:
        return mean_aqi_by_city(df)

    @staticmethod
    def city_mean_with_coords(df: pd.DataFrame) -> pd.DataFrame:
        """Mean AQI per city with lat/lon columns for map visualization."""
        city_df = mean_aqi_by_city(df)
        if city_df.empty:
            return pd.DataFrame()
        city_df["lat"] = city_df[COL_CITY].map(
            lambda c: CITY_COORDINATES.get(c, (None, None))[0]
        )
        city_df["lon"] = city_df[COL_CITY].map(
            lambda c: CITY_COORDINATES.get(c, (None, None))[1]
        )
        return city_df.dropna(subset=["lat", "lon"])

    @staticmethod
    def most_polluted_city(df: pd.DataFrame) -> tuple[str, float]:
        """Return (city_name, mean_aqi) for the worst city."""
        city_df = mean_aqi_by_city(df)
        if city_df.empty:
            return ("—", float("nan"))
        row = city_df.iloc[0]
        return (str(row[COL_CITY]), float(row["aqi_mean"]))

    @staticmethod
    def cleanest_city(df: pd.DataFrame) -> tuple[str, float]:
        """Return (city_name, mean_aqi) for the best city."""
        city_df = mean_aqi_by_city(df)
        if city_df.empty:
            return ("—", float("nan"))
        row = city_df.iloc[-1]
        return (str(row[COL_CITY]), float(row["aqi_mean"]))

    @staticmethod
    def city_count(df: pd.DataFrame) -> int:
        if df.empty or COL_CITY not in df.columns:
            return 0
        return int(df[COL_CITY].nunique())
