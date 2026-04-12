"""Correlation page data access and transforms."""

from __future__ import annotations

from datetime import date
from typing import Literal

import pandas as pd

from dashboard.data.repositories import DatasetRepository
from dashboard.data.schema import COL_AQI, COL_AQI_BUCKET, COL_CITY, COL_DATE

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


class CorrelationData(DatasetRepository):
    """Correlation-specific pipeline on top of shared dataset access."""

    dataset_kind = "city_day"

    @staticmethod
    def validate_required_columns(df: pd.DataFrame) -> list[str]:
        required = [COL_CITY, COL_DATE, COL_AQI_BUCKET, *FEATURE_COLUMNS]
        return [col for col in required if col not in df.columns]

    @staticmethod
    def prepare_base_data(df: pd.DataFrame) -> pd.DataFrame:
        use_cols = [COL_CITY, COL_DATE, COL_AQI_BUCKET, *FEATURE_COLUMNS]
        prepared = df[use_cols].copy()
        prepared[COL_CITY] = prepared[COL_CITY].astype("string")
        prepared[COL_AQI_BUCKET] = prepared[COL_AQI_BUCKET].astype("string")
        prepared[COL_DATE] = pd.to_datetime(prepared[COL_DATE], errors="coerce")
        for col in FEATURE_COLUMNS:
            prepared[col] = pd.to_numeric(prepared[col], errors="coerce")
        return prepared.dropna(subset=[COL_CITY, COL_DATE])

    @staticmethod
    def date_bounds(df: pd.DataFrame) -> tuple[date, date]:
        if df.empty or COL_DATE not in df.columns:
            return date(2015, 1, 1), date(2020, 12, 31)
        dates = pd.to_datetime(df[COL_DATE], errors="coerce").dropna()
        if dates.empty:
            return date(2015, 1, 1), date(2020, 12, 31)
        return dates.min().date(), dates.max().date()

    @staticmethod
    def filter_data(
        df: pd.DataFrame,
        selected_city: str,
        selected_dates: tuple[date, date],
    ) -> pd.DataFrame:
        if df.empty:
            return df.copy()
        start_date, end_date = selected_dates
        row_dates = pd.to_datetime(df[COL_DATE], errors="coerce").dt.date
        mask = (row_dates >= start_date) & (row_dates <= end_date)
        if selected_city != ALL_CITIES:
            mask &= df[COL_CITY].astype(str).eq(selected_city)
        return df.loc[mask].copy()

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: MissingStrategy) -> pd.DataFrame:
        if df.empty:
            return df.copy()
        cleaned = df.copy()
        if strategy == "Fill missing feature values with median":
            medians = cleaned[FEATURE_COLUMNS].median(numeric_only=True)
            cleaned[FEATURE_COLUMNS] = cleaned[FEATURE_COLUMNS].fillna(medians)
        return cleaned.dropna(subset=FEATURE_COLUMNS)

    @staticmethod
    def pearson_matrix(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(index=FEATURE_COLUMNS, columns=FEATURE_COLUMNS)
        return df[FEATURE_COLUMNS].corr(method="pearson")

    @staticmethod
    def severe_pollutant_means(df: pd.DataFrame) -> pd.DataFrame:
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
