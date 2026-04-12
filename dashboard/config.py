"""Dashboard constants: titles, filters, AQI ordering, colors, theming."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "Air_Quality_India_Data" / "processed"

APP_TITLE = "Air Quality in India (2015–2020)"
APP_ICON = "🌫️"

# ---------------------------------------------------------------------------
# AQI colour scale (from redesign spec)
# ---------------------------------------------------------------------------
AQI_COLOR_SCALE: dict[str, dict[str, str]] = {
    "Good":         {"bg": "#A8E5A0", "text": "#1B5E20"},
    "Satisfactory": {"bg": "#D4F1A8", "text": "#33691E"},
    "Moderate":     {"bg": "#FFE082", "text": "#F57F17"},
    "Poor":         {"bg": "#FFAB76", "text": "#BF360C"},
    "Very Poor":    {"bg": "#EF9A9A", "text": "#B71C1C"},
    "Severe":       {"bg": "#CE93D8", "text": "#4A148C"},
}

AQI_RANGES: dict[str, tuple[int, int]] = {
    "Good":         (0, 50),
    "Satisfactory": (51, 100),
    "Moderate":     (101, 200),
    "Poor":         (201, 300),
    "Very Poor":    (301, 400),
    "Severe":       (401, 500),
}

AQI_BUCKET_ORDER: tuple[str, ...] = (
    "Good",
    "Satisfactory",
    "Moderate",
    "Poor",
    "Very Poor",
    "Severe",
)

DANGEROUS_AQI_BUCKETS: frozenset[str] = frozenset({"Poor", "Very Poor", "Severe"})

# ---------------------------------------------------------------------------
# WHO guideline limits (µg/m³; CO in µg/m³ for consistency)
# ---------------------------------------------------------------------------
WHO_LIMITS: dict[str, float] = {
    "PM2.5": 15.0,
    "PM10": 45.0,
    "NO2": 25.0,
    "SO2": 40.0,
    "CO": 4000.0,
    "O3": 100.0,
}

# ---------------------------------------------------------------------------
# Pollutant columns
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Page navigation
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Temporal / trend constants
# ---------------------------------------------------------------------------
WINTER_MONTHS: frozenset[int] = frozenset({11, 12, 1, 2})

TREND_STABLE_THRESHOLD: float = 0.3
TREND_LABELS: dict[str, str] = {
    "improving": "Improving",
    "worsening": "Worsening",
    "stable": "Stable",
}
MIN_TREND_MONTHS: int = 12

# ---------------------------------------------------------------------------
# Chart theming
# ---------------------------------------------------------------------------
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

CHART_LAYOUT_DEFAULTS: dict = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "DM Sans, sans-serif", "color": "#374151"},
    "margin": {"t": 48, "b": 40, "l": 48, "r": 24},
    "hoverlabel": {
        "bgcolor": "#1F2937",
        "font_size": 13,
        "font_family": "DM Sans, sans-serif",
        "font_color": "white",
        "bordercolor": "#1F2937",
    },
}

AQI_THRESHOLD_LINES: list[dict] = [
    {"y": 50,  "color": "#A8E5A0", "label": "Good"},
    {"y": 100, "color": "#FFE082", "label": "Moderate"},
    {"y": 200, "color": "#FFAB76", "label": "Poor"},
    {"y": 300, "color": "#EF9A9A", "label": "Very Poor"},
]
