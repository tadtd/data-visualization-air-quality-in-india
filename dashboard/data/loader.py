"""CSV loading with Streamlit cache and optional missing-file handling.

When data files are not present locally (e.g. on Streamlit Cloud),
the loader automatically downloads them from Kaggle using kagglehub.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.config import DEFAULT_DATA_DIR, KAGGLE_DATASET_HANDLE
from dashboard.data.schema import COL_DATE, COL_DATETIME, DataPaths, DatasetKind

logger = logging.getLogger(__name__)

# Expected CSV filenames in the dataset
_EXPECTED_FILES: dict[str, str] = {
    "city_day": "city_day.csv",
    "city_hour": "city_hour.csv",
    "station_day": "station_day.csv",
    "station_hour": "station_hour.csv",
    "stations": "stations.csv",
}


# ---------------------------------------------------------------------------
# Kaggle auto-download
# ---------------------------------------------------------------------------

def _setup_kaggle_credentials() -> None:
    """Read Kaggle credentials from Streamlit secrets and configure kagglehub.

    Writes credentials to both environment variables AND the standard
    ``~/.kaggle/kaggle.json`` file so that kagglehub can authenticate.
    """
    import json

    username = os.environ.get("KAGGLE_USERNAME", "")
    key = os.environ.get("KAGGLE_KEY", "")

    # Try reading from Streamlit secrets first
    try:
        username = st.secrets.get("KAGGLE_USERNAME", "") or username
        key = st.secrets.get("KAGGLE_KEY", "") or key
    except Exception:
        pass

    if not username or not key:
        logger.warning("Kaggle credentials not found. Private datasets will fail.")
        st.warning(
            "⚠️ Kaggle credentials chưa được cấu hình.\n\n"
            "Hãy thêm vào **Streamlit Cloud → Settings → Secrets**:\n"
            "```toml\n"
            'KAGGLE_USERNAME = "your-username"\n'
            'KAGGLE_KEY = "your-api-key"\n'
            "```"
        )
        return

    # Set environment variables
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = key

    # Write ~/.kaggle/kaggle.json (the standard auth method for kagglehub)
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    if not kaggle_json.exists():
        kaggle_dir.mkdir(parents=True, exist_ok=True)
        kaggle_json.write_text(
            json.dumps({"username": username, "key": key})
        )
        # Restrict permissions on Linux/Mac (Streamlit Cloud runs Linux)
        try:
            kaggle_json.chmod(0o600)
        except OSError:
            pass
        logger.info("Wrote Kaggle credentials to %s", kaggle_json)

    logger.info("Kaggle credentials configured for user '%s'.", username)


def _download_from_kaggle(target_dir: Path) -> None:
    """Download the dataset from Kaggle and copy files to *target_dir*."""
    _setup_kaggle_credentials()

    import kagglehub  # lazy import to avoid slow startup when not needed

    logger.info("Downloading dataset '%s' from Kaggle…", KAGGLE_DATASET_HANDLE)
    try:
        with st.spinner("Đang tải dữ liệu từ Kaggle… Vui lòng đợi."):
            downloaded_path = Path(kagglehub.dataset_download(KAGGLE_DATASET_HANDLE))
    except Exception as exc:
        st.error(
            f"❌ Không thể tải dataset từ Kaggle.\n\n"
            f"**Lỗi:** `{exc}`\n\n"
            f"**Kiểm tra:**\n"
            f"1. Dataset `{KAGGLE_DATASET_HANDLE}` có tồn tại trên Kaggle?\n"
            f"2. Nếu dataset **Private**, hãy thêm Secrets trên Streamlit Cloud:\n"
            f"   - `KAGGLE_USERNAME = \"your-username\"`\n"
            f"   - `KAGGLE_KEY = \"your-api-key\"`\n"
            f"3. Lấy API key tại: https://www.kaggle.com/settings → API → Create New Token"
        )
        st.stop()
        return

    logger.info("Dataset downloaded to: %s", downloaded_path)

    # Ensure destination exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy CSV files from downloaded location to our data dir
    csv_files = list(downloaded_path.rglob("*.csv"))
    if not csv_files:
        st.error("Không tìm thấy file CSV nào trong dataset Kaggle.")
        return

    for src in csv_files:
        dest = target_dir / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
            logger.info("Copied %s → %s", src.name, dest)


def _ensure_data_available(data_dir: Path) -> None:
    """If any expected CSV is missing, attempt Kaggle download."""
    missing = [
        fname
        for fname in _EXPECTED_FILES.values()
        if not (data_dir / fname).is_file()
    ]
    if missing:
        logger.info("Missing files: %s – attempting Kaggle download.", missing)
        _download_from_kaggle(data_dir)


# ---------------------------------------------------------------------------
# Path resolution & CSV loading
# ---------------------------------------------------------------------------

def _resolve_paths(data_dir: Path | str | None = None) -> DataPaths:
    root = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    # Auto-download from Kaggle when files are missing
    _ensure_data_available(root)

    resolved: dict[str, str | None] = {}
    for key, fname in _EXPECTED_FILES.items():
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
