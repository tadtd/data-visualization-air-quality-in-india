# Air Quality in India Dashboard (2015–2020)

This project is part of the course `CSC10108 - Data Visualization` at HCMUS.

## Live dashboard

You can view the deployed Streamlit app here: https://api-in-india.streamlit.app/

## Overview

An interactive dashboard for exploring air quality across Indian cities and monitoring stations. The app supports multiple analysis views:

- AQI overview & city snapshot
- Geography comparison
- Pollutant correlation
- Temporal trends
- Insights & recommendations

## Features

- Shared filters (date range + city selection) across all pages
- AQI color buckets with a colorblind-friendly mode
- Interactive charts (Plotly) across different perspectives
- Automatic data loading from local CSVs, with optional Kaggle auto-download when files are missing

## Data (CSV files)

The dashboard expects the processed dataset files under:

`data/Air_Quality_India_Data/processed/`

Required CSV filenames:

- `city_day.csv`
- `city_hour.csv`
- `station_day.csv`
- `station_hour.csv`
- `stations.csv`

Original dataset on Kaggle (source):
https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india

## Local Installation & Run

1. Use Python `>= 3.13`.
2. Install dependencies with `uv` (reads `pyproject.toml`):

```bash
uv sync
```

3. Run the app:

```bash
uv run streamlit run main.py
```

## Folder Structure

- `main.py`: Streamlit entrypoint
- `dashboard/`: dashboard application code
  - `router.py`: tab navigation (Overview, Geography, Correlation, Temporal, Insights)
  - `pages/`: page implementations
  - `data/`: dataset loading, schemas, and transforms
  - `components/`: reusable UI components (filters, charts, KPI cards)
- `preprocessing/`: helper scripts (e.g., missing value handling for the raw dataset)