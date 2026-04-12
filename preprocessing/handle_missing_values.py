"""Utilities to preprocess missing values in the air-quality datasets.

Example:
    uv run python preprocessing/handle_missing_values.py
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DatasetConfig:
    filename: str
    entity_col: str | None = None
    time_col: str | None = None


DATASETS: dict[str, DatasetConfig] = {
    "city_day": DatasetConfig(
        filename="city_day.csv",
        entity_col="City",
        time_col="Date",
    ),
    "city_hour": DatasetConfig(
        filename="city_hour.csv",
        entity_col="City",
        time_col="Datetime",
    ),
    "station_day": DatasetConfig(
        filename="station_day.csv",
        entity_col="StationId",
        time_col="Date",
    ),
    "station_hour": DatasetConfig(
        filename="station_hour.csv",
        entity_col="StationId",
        time_col="Datetime",
    ),
    "stations": DatasetConfig(
        filename="stations.csv",
        entity_col="StationId",
        time_col=None,
    ),
}

NUMERIC_COLUMNS = [
    "PM2.5",
    "PM10",
    "NO",
    "NO2",
    "NOx",
    "NH3",
    "CO",
    "SO2",
    "O3",
    "Benzene",
    "Toluene",
    "Xylene",
    "AQI",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess missing values in Air_Quality_India_Data CSV files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data") / "Air_Quality_India_Data",
        help="Folder containing raw CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data") / "Air_Quality_India_Data" / "processed",
        help="Folder to write cleaned CSV files and report.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=sorted(DATASETS.keys()),
        default=sorted(DATASETS.keys()),
        help="Dataset keys to process.",
    )
    return parser.parse_args()


def _group_interpolate(series: pd.Series) -> pd.Series:
    return series.interpolate(method="linear", limit_direction="both")


def fill_numeric_missing(
    df: pd.DataFrame, *, entity_col: str | None, time_col: str | None
) -> pd.DataFrame:
    numeric_cols = [col for col in NUMERIC_COLUMNS if col in df.columns]
    if not numeric_cols:
        return df

    if time_col and time_col in df.columns:
        sort_cols = [c for c in [entity_col, time_col] if c and c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

        if entity_col and entity_col in df.columns:
            interpolated = df.groupby(entity_col, dropna=False)[col].transform(
                _group_interpolate
            )
            df[col] = interpolated

            group_median = df.groupby(entity_col, dropna=False)[col].transform("median")
            df[col] = df[col].fillna(group_median)
        else:
            df[col] = _group_interpolate(df[col])

        global_median = df[col].median()
        if pd.notna(global_median):
            df[col] = df[col].fillna(global_median)

    return df


def fill_categorical_missing(df: pd.DataFrame) -> pd.DataFrame:
    if "AQI_Bucket" in df.columns:
        df["AQI_Bucket"] = df["AQI_Bucket"].fillna("Unknown")

    if "Status" in df.columns:
        mode = df["Status"].mode(dropna=True)
        fallback = mode.iloc[0] if not mode.empty else "Unknown"
        df["Status"] = df["Status"].fillna(fallback)

    return df


def preprocess_frame(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    if config.time_col and config.time_col in df.columns:
        df[config.time_col] = pd.to_datetime(df[config.time_col], errors="coerce")

    df = fill_numeric_missing(df, entity_col=config.entity_col, time_col=config.time_col)
    df = fill_categorical_missing(df)
    return df


def process_dataset(input_dir: Path, output_dir: Path, dataset_key: str) -> dict[str, int]:
    config = DATASETS[dataset_key]
    input_path = input_dir / config.filename
    if not input_path.exists():
        raise FileNotFoundError(f"Missing file: {input_path}")

    df = pd.read_csv(input_path)
    missing_before = int(df.isna().sum().sum())

    cleaned_df = preprocess_frame(df, config)
    missing_after = int(cleaned_df.isna().sum().sum())

    output_path = output_dir / config.filename
    cleaned_df.to_csv(output_path, index=False)

    return {
        "dataset": dataset_key,
        "rows": int(len(cleaned_df)),
        "missing_before": missing_before,
        "missing_after": missing_after,
    }


def main() -> None:
    args = parse_args()
    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    report_rows: list[dict[str, int]] = []
    for key in args.datasets:
        report_rows.append(process_dataset(input_dir, output_dir, key))

    report_df = pd.DataFrame(report_rows).sort_values("dataset")
    report_path = output_dir / "missing_values_report.csv"
    report_df.to_csv(report_path, index=False)

    print("Preprocessing complete.")
    print(f"Processed datasets: {', '.join(args.datasets)}")
    print(f"Output directory: {output_dir}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
