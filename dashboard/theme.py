"""Global CSS injection and HTML helper functions for the dashboard theme."""

from __future__ import annotations

import streamlit as st

from dashboard.config import AQI_COLOR_SCALE, AQI_RANGES


def inject_theme() -> None:
    """Inject global CSS rules once per session (uses Streamlit theme CSS variables)."""
    st.markdown(
        """
        <style>
        /*
         * Theme tokens: Streamlit injects --st-* on the app root (see theming docs).
         * Fallbacks match Streamlit light defaults when vars are unavailable.
         */
        /* ---- AQI pill badge ---- */
        .aqi-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 14px;
            font-weight: 600;
            font-size: 13px;
            line-height: 1.4;
            white-space: nowrap;
        }

        /* ---- Section divider ---- */
        .section-divider {
            border: none;
            border-top: 1px solid var(--st-border-color, rgba(49, 51, 63, 0.12));
            margin: 28px 0;
        }

        /* ---- Hero number (AQI tint still applied inline on the span) ---- */
        .hero-number {
            font-size: 56px;
            font-weight: 700;
            line-height: 1.1;
        }

        /* Do not style div[data-testid="stMetric"] — native metrics follow the active theme. */
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
    colors = AQI_COLOR_SCALE.get(bucket, {"bg": "#E5E7EB", "text": "#374151"})
    return (
        f'<span class="aqi-pill" '
        f'style="background:{colors["bg"]};color:{colors["text"]}">'
        f"{bucket}</span>"
    )


def render_aqi_pill(bucket: str) -> None:
    """Render an AQI pill badge inline."""
    st.markdown(aqi_pill_html(bucket), unsafe_allow_html=True)


def hero_number_html(value: str | int | float, bucket: str) -> str:
    """Return HTML for the hero AQI number with category color."""
    colors = AQI_COLOR_SCALE.get(bucket, {"bg": "#E5E7EB", "text": "#374151"})
    return (
        f'<span class="hero-number" style="color:{colors["text"]}">'
        f"{value}</span>"
    )


def section_divider() -> None:
    """Render a thin visual divider between sections."""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
