"""Dashboard constants: titles, filters, AQI ordering, colors."""

from __future__ import annotations

from pathlib import Path

# Default data directory (Kaggle-style layout under project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "Air_Quality_India_Data"

APP_TITLE = "Air Quality in India (2015–2020)"
APP_ICON = "🌫️"

# AQI bucket display order (worst last for stacked bars / ordered legends)
AQI_BUCKET_ORDER: tuple[str, ...] = (
    "Good",
    "Satisfactory",
    "Moderate",
    "Poor",
    "Very Poor",
    "Severe",
)

# Dangerous buckets for frequency analysis (proposal)
DANGEROUS_AQI_BUCKETS: frozenset[str] = frozenset({"Poor", "Very Poor", "Severe"})

# Pollutant columns for correlation / selection (subset from proposal)
POLLUTANT_COLUMNS: tuple[str, ...] = (
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
)

PAGE_KEYS: tuple[str, ...] = (
    "overview",
    "temporal",
    "geography",
    "correlation",
    "insights",
)

PAGE_LABELS: dict[str, str] = {
    "overview": "Overview",
    "temporal": "Temporal Analysis",
    "geography": "Geographic Comparison",
    "correlation": "Pollutant Correlation",
    "insights": "Insights & Recommendations",
}

# Winter months (Nov–Feb) — high-pollution season in India
WINTER_MONTHS: frozenset[int] = frozenset({11, 12, 1, 2})

# Trend classification: slope in AQI units/month
TREND_STABLE_THRESHOLD: float = 0.3  # |slope| below this → "Stable"
TREND_LABELS: dict[str, str] = {
    "improving": "Improving",
    "worsening": "Worsening",
    "stable": "Stable",
}

# Minimum months of data required for a city trend slope to be computed
MIN_TREND_MONTHS: int = 12

# Plotly-friendly qualitative palette (colorblind-friendly-ish)
CHART_COLOR_SEQUENCE: list[str] = [
    "#0173B2",
    "#DE8F05",
    "#029E73",
    "#CC78BC",
    "#CA9161",
    "#949494",
    "#ECE133",
    "#56B4E9",
]
