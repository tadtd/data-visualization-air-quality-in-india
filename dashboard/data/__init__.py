"""Shared dashboard data access, filtering, and transforms."""

from dashboard.data.loader import data_status_message, load_dataset
from dashboard.data.repositories import DatasetRepository, load_dataset_frame
from dashboard.data.schema import FilterState
from dashboard.data.transforms import (
    apply_filters,
    count_dangerous_days_by_city,
    default_date_range_from_df,
    list_cities,
    mean_aqi_by_city,
    mean_aqi_by_month,
    mean_aqi_by_state,
    merge_state_info,
    summarize_aqi_kpis,
)

__all__ = [
    "FilterState",
    "DatasetRepository",
    "apply_filters",
    "count_dangerous_days_by_city",
    "data_status_message",
    "default_date_range_from_df",
    "list_cities",
    "load_dataset",
    "load_dataset_frame",
    "mean_aqi_by_city",
    "mean_aqi_by_month",
    "mean_aqi_by_state",
    "merge_state_info",
    "summarize_aqi_kpis",
]
