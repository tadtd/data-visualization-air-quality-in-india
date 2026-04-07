"""Column names and filter state contract for dashboard data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

# Dataset kinds supported by loader
DatasetKind = Literal["city_day", "city_hour", "station_day", "station_hour", "stations"]

# Canonical column names (Kaggle India AQI dataset)
COL_CITY = "City"
COL_STATION_ID = "StationId"
COL_DATE = "Date"
COL_DATETIME = "Datetime"
COL_AQI = "AQI"
COL_AQI_BUCKET = "AQI_Bucket"

TIME_COLUMNS = (COL_DATE, COL_DATETIME)


@dataclass
class FilterState:
    """Shared filter model across pages."""

    date_start: date
    date_end: date
    cities: list[str] = field(default_factory=list)
    pollutants: list[str] = field(default_factory=list)
    aqi_buckets: list[str] = field(default_factory=list)


@dataclass
class DataPaths:
    """Resolved paths to CSV files."""

    data_dir: str
    city_day: str | None = None
    city_hour: str | None = None
    station_day: str | None = None
    station_hour: str | None = None
    stations: str | None = None
