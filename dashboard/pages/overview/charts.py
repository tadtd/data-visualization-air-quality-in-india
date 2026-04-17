"""Overview page chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.charts import add_aqi_reference_lines, apply_chart_theme, empty_chart
from dashboard.config import get_aqi_colors, get_chart_color_sequence
from dashboard.theme import aqi_bucket_for_value


class OverviewCharts:
    """Chart builders for the Overview page."""

    @staticmethod
    def monthly_trend(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Xu hướng AQI trung bình theo tháng")

        colors = get_chart_color_sequence()
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["year_month"],
                y=df["aqi_mean"],
                mode="lines",
                fill="tozeroy",
                line=dict(color=colors[0], width=2),
                fillcolor="rgba(1,115,178,0.12)",
                name="AQI trung bình",
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

        fig.update_layout(
            title="Xu hướng AQI trung bình toàn quốc theo tháng",
            xaxis_title="Tháng",
            yaxis_title="AQI",
            height=400,
        )
        fig.update_xaxes(tickangle=-45, nticks=12)
        return apply_chart_theme(fig)

    @staticmethod
    def city_snapshot(df: pd.DataFrame, *, top_n: int = 8) -> go.Figure:
        if df.empty:
            return empty_chart("Xếp hạng AQI theo thành phố")

        top = df.head(top_n)
        bottom = df.tail(top_n).sort_values("aqi_mean", ascending=True)
        sub = pd.concat([top, bottom], ignore_index=True).drop_duplicates(subset=["City"])

        aqi_colors = get_aqi_colors()
        colors = [
            aqi_colors.get(aqi_bucket_for_value(v), {"bg": "#E5E7EB"})["bg"]
            for v in sub["aqi_mean"]
        ]
        fig = go.Figure(
            go.Bar(
                x=sub["City"],
                y=sub["aqi_mean"],
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br>AQI trung bình: %{y:.1f}<extra></extra>",
            )
        )
        fig.update_layout(
            title=f"Top / Bottom {top_n} thành phố theo AQI trung bình",
            xaxis_title="",
            yaxis_title="AQI trung bình",
            height=450,
            showlegend=False,
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def india_map(df: pd.DataFrame) -> go.Figure:
        """Scatter map of Indian cities colored by mean AQI."""
        if df.empty:
            return empty_chart("Bản đồ AQI các thành phố Ấn Độ")

        aqi_colors = get_aqi_colors()
        df = df.copy()
        df["bucket"] = df["aqi_mean"].apply(aqi_bucket_for_value)
        df["color"] = df["bucket"].map(
            lambda b: aqi_colors.get(b, {"bg": "#E5E7EB"})["bg"]
        )
        # Scale marker size: min 12, max 40
        aqi_min, aqi_max = df["aqi_mean"].min(), df["aqi_mean"].max()
        if aqi_max > aqi_min:
            df["marker_size"] = 12 + (df["aqi_mean"] - aqi_min) / (aqi_max - aqi_min) * 28
        else:
            df["marker_size"] = 20

        from dashboard.config import AQI_BUCKET_VI
        df["bucket_vi"] = df["bucket"].map(lambda b: AQI_BUCKET_VI.get(b, b))

        fig = go.Figure()
        fig.add_trace(
            go.Scattermapbox(
                lat=df["lat"],
                lon=df["lon"],
                mode="markers+text",
                marker=dict(
                    size=df["marker_size"],
                    color=df["color"],
                    opacity=0.85,
                    sizemode="diameter",
                ),
                text=df["City"],
                textposition="top center",
                textfont=dict(size=10, family="Be Vietnam Pro"),
                customdata=df[["aqi_mean", "bucket_vi"]].values,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "AQI trung bình: %{customdata[0]:.1f}<br>"
                    "Mức: %{customdata[1]}<extra></extra>"
                ),
            )
        )
        fig.update_layout(
            title="Bản đồ AQI trung bình các thành phố Ấn Độ",
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=22.5, lon=79.0),
                zoom=4,
            ),
            height=550,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
        )
        return apply_chart_theme(fig)
