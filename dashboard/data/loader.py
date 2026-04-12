"""CSV loading with Streamlit cache and optional missing-file handling."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.config import DEFAULT_DATA_DIR
from dashboard.data.schema import COL_DATE, COL_DATETIME, DataPaths, DatasetKind


def _resolve_paths(data_dir: Path | str | None = None) -> DataPaths:
    root = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    names = {
        "city_day": "city_day.csv",
        "city_hour": "city_hour.csv",
        "station_day": "station_day.csv",
        "station_hour": "station_hour.csv",
        "stations": "stations.csv",
    }
    resolved: dict[str, str | None] = {}
    for key, fname in names.items():
        p = root / fname
        resolved[key] = str(p) if p.is_file() else None
    return DataPaths(data_dir=str(root), **resolved)


@st.cache_data(show_spinner="Loading data…")
def load_csv(path: str, *, parse_dates: list[str] | None = None) -> pd.DataFrame:
    """Load a single CSV; parse_dates applied when columns exist."""
    df = pd.read_csv(path)
    if parse_dates:
        for c in parse_dates:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def load_dataset(kind: DatasetKind, data_dir: Path | str | None = None) -> pd.DataFrame | None:
    """Load a dataset by kind; returns None if file missing."""
    paths = _resolve_paths(data_dir)
    path_map: dict[DatasetKind, str | None] = {
        "city_day": paths.city_day,
        "city_hour": paths.city_hour,
        "station_day": paths.station_day,
        "station_hour": paths.station_hour,
        "stations": paths.stations,
    }
    p = path_map.get(kind)
    if not p:
        return None
    parse_dates: list[str] = []
    if kind in ("city_day", "station_day"):
        parse_dates = [COL_DATE]
    elif kind in ("city_hour", "station_hour"):
        parse_dates = [COL_DATETIME]
    return load_csv(p, parse_dates=parse_dates)


def data_status_message(data_dir: Path | str | None = None) -> str | None:
    """Human-readable status for sidebar when CSVs are absent."""
    paths = _resolve_paths(data_dir)
    missing = [
        name
        for name, p in [
            ("city_day.csv", paths.city_day),
            ("city_hour.csv", paths.city_hour),
            ("station_day.csv", paths.station_day),
            ("station_hour.csv", paths.station_hour),
            ("stations.csv", paths.stations),
        ]
        if p is None
    ]
    if missing:
        return (
            f"Place Kaggle CSVs under `{paths.data_dir}`. Missing: {', '.join(missing)}"
        )
    
