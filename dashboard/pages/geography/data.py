"""Geography page data access and aggregations."""

from __future__ import annotations

import pandas as pd

from dashboard.data.loader import load_dataset
from dashboard.data.repositories import DatasetRepository
from dashboard.data.schema import FilterState
from dashboard.data.transforms import (
    count_dangerous_days_by_city,
    mean_aqi_by_city,
    mean_aqi_by_state,
    merge_state_info,
)


class GeographyData(DatasetRepository):
    """Data access and city-level summaries for the Geography page."""

    dataset_kind = "city_day"

    @staticmethod
    def filter_frame(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
        return GeographyData.apply_filter_state(df, filters)

    @staticmethod
    def city_mean(df: pd.DataFrame) -> pd.DataFrame:
        return mean_aqi_by_city(df)

    @staticmethod
    def dangerous_day_counts(df: pd.DataFrame) -> pd.DataFrame:
        return count_dangerous_days_by_city(df)

    @staticmethod
    def state_mean(df: pd.DataFrame) -> pd.DataFrame:
        """Mean AQI per state (joins stations.csv for city→state mapping)."""
        stations = load_dataset("stations")
        if stations is None:
            return pd.DataFrame()
        merged = merge_state_info(df, stations)
        return mean_aqi_by_state(merged)
