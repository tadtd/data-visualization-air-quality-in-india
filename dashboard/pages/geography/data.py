"""Geography page data access (city-level aggregates only)."""

from __future__ import annotations

import pandas as pd

from dashboard.data.repositories import DatasetRepository
from dashboard.data.transforms import mean_aqi_by_city


class GeographyData(DatasetRepository):
    """City-day frame for the Geography tab."""

    dataset_kind = "city_day"

    @staticmethod
    def city_mean(df: pd.DataFrame) -> pd.DataFrame:
        return mean_aqi_by_city(df)
