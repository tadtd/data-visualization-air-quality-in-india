"""Geography page chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.components.charts import apply_chart_theme, empty_chart
from dashboard.config import AQI_COLOR_SCALE, CHART_COLOR_SEQUENCE, DANGEROUS_AQI_BUCKETS
from dashboard.theme import aqi_bucket_for_value


class GeographyCharts:
    """Chart builders for the Geography page."""

    @staticmethod
    def city_mean_ranking(df: pd.DataFrame, *, top_n: int = 10) -> go.Figure:
        if df.empty:
            return empty_chart("City Mean AQI Ranking")
        top = df.head(top_n)
        bottom = df.tail(top_n).sort_values("aqi_mean", ascending=True)
        sub = pd.concat([top, bottom], ignore_index=True).drop_duplicates(subset=["City"])

        colors = [
            AQI_COLOR_SCALE.get(aqi_bucket_for_value(v), {"bg": "#E5E7EB"})["bg"]
            for v in sub["aqi_mean"]
        ]
        fig = go.Figure(
            go.Bar(
                x=sub["City"], y=sub["aqi_mean"],
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br>Mean AQI: %{y:.1f}<extra></extra>",
            )
        )
        fig.update_layout(
            title=f"Top / Bottom {top_n} Cities by Mean AQI",
            height=450, showlegend=False,
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def dangerous_days(df: pd.DataFrame, *, top_n: int = 15) -> go.Figure:
        if df.empty:
            return empty_chart("Dangerous-Day Counts")
        sub = df.head(top_n)
        fig = go.Figure(
            go.Bar(
                x=sub["City"], y=sub["danger_days"],
                marker_color=AQI_COLOR_SCALE["Poor"]["bg"],
                hovertemplate="<b>%{x}</b><br>Dangerous days: %{y}<extra></extra>",
            )
        )
        fig.update_layout(
            title=f"Days in {', '.join(sorted(DANGEROUS_AQI_BUCKETS))} (Top {top_n})",
            height=450, showlegend=False,
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def state_ranking_bar(df: pd.DataFrame) -> go.Figure:
        """Horizontal bar chart ranking states by mean AQI."""
        if df.empty:
            return empty_chart("State Mean AQI Ranking")
        sub = df.sort_values("aqi_mean", ascending=True)
        colors = [
            AQI_COLOR_SCALE.get(aqi_bucket_for_value(v), {"bg": "#E5E7EB"})["bg"]
            for v in sub["aqi_mean"]
        ]
        fig = go.Figure(
            go.Bar(
                y=sub["State"], x=sub["aqi_mean"],
                orientation="h",
                marker_color=colors,
                text=sub["aqi_mean"].round(1),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Mean AQI: %{x:.1f}<extra></extra>",
            )
        )
        fig.update_layout(
            title="State Mean AQI Ranking (worst → best)",
            height=max(400, 24 * len(sub) + 80),
            margin=dict(l=140, r=40, t=50, b=30),
            showlegend=False,
        )
        return apply_chart_theme(fig)
