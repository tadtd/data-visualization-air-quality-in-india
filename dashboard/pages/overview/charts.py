"""Overview page chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.charts import add_aqi_reference_lines, apply_chart_theme, empty_chart
from dashboard.config import AQI_COLOR_SCALE, CHART_COLOR_SEQUENCE
from dashboard.theme import aqi_bucket_for_value


class OverviewCharts:
    """Chart builders for the Overview page."""

    @staticmethod
    def monthly_trend(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("National Monthly AQI Trend")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["year_month"],
                y=df["aqi_mean"],
                mode="lines",
                fill="tozeroy",
                line=dict(color=CHART_COLOR_SEQUENCE[0], width=2),
                fillcolor="rgba(1,115,178,0.12)",
                name="Mean AQI",
            )
        )
        add_aqi_reference_lines(fig)

        if "2020-03" in df["year_month"].values:
            fig.add_vline(x="2020-03", line_dash="dot", line_color="grey", line_width=1)
            fig.add_annotation(
                x="2020-03", y=1, yref="paper", text="COVID-19",
                showarrow=False, font=dict(size=10, color="grey"),
                xanchor="left", yanchor="top",
            )

        fig.update_layout(title="National Monthly AQI Trend", height=400)
        fig.update_xaxes(tickangle=-45, nticks=12)
        return apply_chart_theme(fig)

    @staticmethod
    def city_snapshot(df: pd.DataFrame, *, top_n: int = 8) -> go.Figure:
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
                x=sub["City"],
                y=sub["aqi_mean"],
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br>Mean AQI: %{y:.1f}<extra></extra>",
            )
        )
        fig.update_layout(
            title=f"Top / Bottom {top_n} Cities by Mean AQI",
            height=450,
            showlegend=False,
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)
