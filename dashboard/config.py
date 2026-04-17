"""Dashboard constants: titles, filters, AQI ordering, colors, theming."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "Air_Quality_India_Data"

APP_TITLE = "Chất lượng Không khí tại Ấn Độ (2015–2020)"
APP_ICON = "🌫️"

# ---------------------------------------------------------------------------
# AQI colour scale — normal mode
# ---------------------------------------------------------------------------
AQI_COLOR_SCALE: dict[str, dict[str, str]] = {
    "Good":         {"bg": "#A8E5A0", "text": "#1B5E20"},
    "Satisfactory": {"bg": "#D4F1A8", "text": "#33691E"},
    "Moderate":     {"bg": "#FFE082", "text": "#F57F17"},
    "Poor":         {"bg": "#FFAB76", "text": "#BF360C"},
    "Very Poor":    {"bg": "#EF9A9A", "text": "#B71C1C"},
    "Severe":       {"bg": "#CE93D8", "text": "#4A148C"},
}

# AQI colour scale — colorblind-safe (Okabe-Ito inspired)
AQI_COLOR_SCALE_CB: dict[str, dict[str, str]] = {
    "Good":         {"bg": "#009E73", "text": "#FFFFFF"},
    "Satisfactory": {"bg": "#56B4E9", "text": "#000000"},
    "Moderate":     {"bg": "#E69F00", "text": "#000000"},
    "Poor":         {"bg": "#F0E442", "text": "#000000"},
    "Very Poor":    {"bg": "#D55E00", "text": "#FFFFFF"},
    "Severe":       {"bg": "#CC79A7", "text": "#FFFFFF"},
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

# Vietnamese display names for AQI buckets
AQI_BUCKET_VI: dict[str, str] = {
    "Good": "Tốt",
    "Satisfactory": "Khá",
    "Moderate": "Trung bình",
    "Poor": "Kém",
    "Very Poor": "Rất kém",
    "Severe": "Nguy hiểm",
}

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
# Page navigation (must match dashboard/router.py tab order)
# ---------------------------------------------------------------------------
PAGE_KEYS: tuple[str, ...] = (
    "overview",
    "geography",
    "correlation",
    "temporal",
    "insights",
)

PAGE_LABELS: dict[str, str] = {
    "overview": "Tổng quan",
    "geography": "So sánh địa lý",
    "correlation": "Tương quan ô nhiễm",
    "temporal": "Phân tích thời gian",
    "insights": "Nhận định & Khuyến nghị",
}

# ---------------------------------------------------------------------------
# Temporal / trend constants
# ---------------------------------------------------------------------------
WINTER_MONTHS: frozenset[int] = frozenset({11, 12, 1, 2})

TREND_STABLE_THRESHOLD: float = 0.3
TREND_LABELS: dict[str, str] = {
    "improving": "Cải thiện",
    "worsening": "Xấu đi",
    "stable": "Ổn định",
}
MIN_TREND_MONTHS: int = 12

# ---------------------------------------------------------------------------
# Chart theming — normal mode
# ---------------------------------------------------------------------------
CHART_RANK_POLLUTED = "#E74C3C"
CHART_RANK_CLEAN = "#2ECC71"
CHART_RANK_CONTINUOUS_SCALE: str = "RdYlGn_r"

CHART_DANGER_BUCKET_COLORS: dict[str, str] = {
    "Poor": "#F39C12",
    "Very Poor": "#E74C3C",
    "Severe": "#8E44AD",
}

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

# Colorblind-safe alternatives
CHART_RANK_POLLUTED_CB = "#D55E00"
CHART_RANK_CLEAN_CB = "#009E73"
CHART_RANK_CONTINUOUS_SCALE_CB: str = "Cividis"

CHART_DANGER_BUCKET_COLORS_CB: dict[str, str] = {
    "Poor": "#E69F00",
    "Very Poor": "#D55E00",
    "Severe": "#CC79A7",
}

CHART_COLOR_SEQUENCE_CB: list[str] = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#D55E00",
    "#56B4E9",
    "#F0E442",
    "#000000",
]

AQI_THRESHOLD_LINES: list[dict] = [
    {"y": 50,  "color": "#A8E5A0", "label": "Tốt"},
    {"y": 100, "color": "#FFE082", "label": "Trung bình"},
    {"y": 200, "color": "#FFAB76", "label": "Kém"},
    {"y": 300, "color": "#EF9A9A", "label": "Rất kém"},
]

AQI_THRESHOLD_LINES_CB: list[dict] = [
    {"y": 50,  "color": "#009E73", "label": "Tốt"},
    {"y": 100, "color": "#E69F00", "label": "Trung bình"},
    {"y": 200, "color": "#F0E442", "label": "Kém"},
    {"y": 300, "color": "#D55E00", "label": "Rất kém"},
]

# ---------------------------------------------------------------------------
# Dynamic color getters (read colorblind toggle from session state)
# ---------------------------------------------------------------------------

def is_colorblind_mode() -> bool:
    """Return True if colorblind mode is enabled."""
    return st.session_state.get("colorblind_mode", False)


def get_aqi_colors() -> dict[str, dict[str, str]]:
    return AQI_COLOR_SCALE_CB if is_colorblind_mode() else AQI_COLOR_SCALE


def get_chart_color_sequence() -> list[str]:
    return CHART_COLOR_SEQUENCE_CB if is_colorblind_mode() else CHART_COLOR_SEQUENCE


def get_danger_bucket_colors() -> dict[str, str]:
    return CHART_DANGER_BUCKET_COLORS_CB if is_colorblind_mode() else CHART_DANGER_BUCKET_COLORS


def get_rank_polluted() -> str:
    return CHART_RANK_POLLUTED_CB if is_colorblind_mode() else CHART_RANK_POLLUTED


def get_rank_clean() -> str:
    return CHART_RANK_CLEAN_CB if is_colorblind_mode() else CHART_RANK_CLEAN


def get_rank_continuous_scale() -> str:
    return CHART_RANK_CONTINUOUS_SCALE_CB if is_colorblind_mode() else CHART_RANK_CONTINUOUS_SCALE


def get_aqi_threshold_lines() -> list[dict]:
    return AQI_THRESHOLD_LINES_CB if is_colorblind_mode() else AQI_THRESHOLD_LINES


# ---------------------------------------------------------------------------
# City coordinates (lat, lon) for map visualization
# ---------------------------------------------------------------------------
CITY_COORDINATES: dict[str, tuple[float, float]] = {
    "Ahmedabad":          (23.0225, 72.5714),
    "Aizawl":             (23.7271, 92.7176),
    "Amaravati":          (16.5131, 80.5150),
    "Amritsar":           (31.6340, 74.8723),
    "Bengaluru":          (12.9716, 77.5946),
    "Bhopal":             (23.2599, 77.4126),
    "Brajrajnagar":       (21.8167, 83.9167),
    "Chandigarh":         (30.7333, 76.7794),
    "Chennai":            (13.0827, 80.2707),
    "Coimbatore":         (11.0168, 76.9558),
    "Delhi":              (28.7041, 77.1025),
    "Ernakulam":          (9.9816,  76.2999),
    "Gurugram":           (28.4595, 77.0266),
    "Guwahati":           (26.1445, 91.7362),
    "Hyderabad":          (17.3850, 78.4867),
    "Jaipur":             (26.9124, 75.7873),
    "Jorapokhar":         (23.7107, 86.4120),
    "Kochi":              (9.9312,  76.2673),
    "Kolkata":            (22.5726, 88.3639),
    "Lucknow":            (26.8467, 80.9462),
    "Mumbai":             (19.0760, 72.8777),
    "Patna":              (25.6093, 85.1376),
    "Shillong":           (25.5788, 91.8933),
    "Talcher":            (20.9517, 85.2133),
    "Thiruvananthapuram": (8.5241,  76.9366),
    "Visakhapatnam":      (17.6868, 83.2185),
}
