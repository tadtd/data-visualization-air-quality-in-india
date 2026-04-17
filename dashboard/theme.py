"""Global CSS injection and HTML helper functions for the dashboard theme."""

from __future__ import annotations

import streamlit as st

from dashboard.config import get_aqi_colors, AQI_RANGES


def inject_theme() -> None:
    """Inject global CSS rules once per session — Be Vietnam Pro font + theme tokens."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap');
        /* ---- Global font (exclude Material Icons/Symbols used by Streamlit) ---- */
        .stApp,
        .stApp *:not([class*="material-icons"]):not([class*="material-symbols"]):not([data-testid="stIconMaterial"]):not(.icon) {
            font-family: 'Be Vietnam Pro', sans-serif !important;
        }

        /* ---- AQI pill badge ---- */
        .aqi-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 14px;
            font-weight: 600;
            font-size: 13px;
            line-height: 1.4;
            white-space: nowrap;
            letter-spacing: 0.02em;
        }

        /* ---- Section divider ---- */
        .section-divider {
            border: none;
            border-top: 1px solid var(--st-border-color, rgba(49, 51, 63, 0.12));
            margin: 24px 0;
        }

        /* ---- Hero number ---- */
        .hero-number {
            font-size: 56px;
            font-weight: 700;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }

        /* ---- Insight caption ---- */
        .chart-insight {
            font-size: 13px;
            color: #6B7280;
            margin-top: -8px;
            margin-bottom: 16px;
            padding-left: 4px;
            border-left: 3px solid #D1D5DB;
            padding: 4px 0 4px 10px;
            font-style: italic;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def aqi_bucket_for_value(aqi: float | int | None) -> str:
    """Return the AQI bucket name for a numeric value."""
    if aqi is None or (isinstance(aqi, float) and (aqi != aqi)):  # NaN check
        return "Moderate"
    for bucket, (lo, hi) in AQI_RANGES.items():
        if lo <= aqi <= hi:
            return bucket
    return "Severe" if aqi > 400 else "Good"


def aqi_pill_html(bucket: str) -> str:
    """Return an HTML <span> for the AQI category pill."""
    colors = get_aqi_colors().get(bucket, {"bg": "#E5E7EB", "text": "#374151"})
    from dashboard.config import AQI_BUCKET_VI
    label = AQI_BUCKET_VI.get(bucket, bucket)
    return (
        f'<span class="aqi-pill" '
        f'style="background:{colors["bg"]};color:{colors["text"]}">'
        f"{label}</span>"
    )


def render_aqi_pill(bucket: str) -> None:
    """Render an AQI pill badge inline."""
    st.markdown(aqi_pill_html(bucket), unsafe_allow_html=True)


def hero_number_html(value: str | int | float, bucket: str) -> str:
    """Return HTML for the hero AQI number with category color."""
    colors = get_aqi_colors().get(bucket, {"bg": "#E5E7EB", "text": "#374151"})
    return (
        f'<span class="hero-number" style="color:{colors["text"]}">'
        f"{value}</span>"
    )


def section_divider() -> None:
    """Render a thin visual divider between sections."""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


def chart_insight(text: str) -> None:
    """Render a short insight caption below a chart."""
    st.markdown(f'<p class="chart-insight">💡 {text}</p>', unsafe_allow_html=True)
