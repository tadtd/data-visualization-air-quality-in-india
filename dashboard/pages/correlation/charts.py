"""Correlation page chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.charts import apply_chart_theme
from dashboard.config import AQI_COLOR_SCALE, WHO_LIMITS
from dashboard.data.schema import COL_AQI, COL_AQI_BUCKET, COL_CITY, COL_DATE
from dashboard.pages.correlation.data import POLLUTANT_COLUMNS
from dashboard.theme import aqi_bucket_for_value


class CorrelationCharts:
    """Plotly builders mapped to each analysis question."""

    @staticmethod
    def empty_state(title: str, message: str) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text=message, x=0.5, y=0.5,
            xref="paper", yref="paper", showarrow=False,
            font=dict(color="#9CA3AF"),
        )
        fig.update_layout(
            title=title, height=520,
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
        return apply_chart_theme(fig)

    @staticmethod
    def pearson_heatmap(corr: pd.DataFrame) -> go.Figure:
        if corr.empty or corr.isna().all().all():
            return CorrelationCharts.empty_state(
                "Pearson Correlation Heatmap",
                "No complete rows available for correlation.",
            )
        fig = px.imshow(
            corr, text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1, aspect="auto",
            labels=dict(color="Pearson r"),
        )
        fig.update_layout(title="Pearson Correlation Heatmap", height=520)
        fig.update_xaxes(side="bottom")
        return apply_chart_theme(fig)

    @staticmethod
    def aqi_scatter(df: pd.DataFrame, selected_pollutant: str) -> go.Figure:
        if df.empty:
            return CorrelationCharts.empty_state(
                f"{selected_pollutant} vs AQI",
                "No rows available for selected filters.",
            )
        bucket_colors = {b: c["bg"] for b, c in AQI_COLOR_SCALE.items()}
        df = df.copy()
        if COL_AQI_BUCKET in df.columns:
            color_col = COL_AQI_BUCKET
        else:
            df["_bucket"] = df[COL_AQI].apply(aqi_bucket_for_value)
            color_col = "_bucket"

        fig = px.scatter(
            df, x=selected_pollutant, y=COL_AQI,
            color=color_col,
            color_discrete_map=bucket_colors,
            hover_data={
                COL_CITY: True,
                COL_DATE: "|%Y-%m-%d",
                selected_pollutant: ":.2f",
                COL_AQI: ":.2f",
            },
            opacity=0.6, render_mode="webgl",
        )
        fig.update_traces(marker=dict(size=5))
        fig.update_layout(
            title=f"{selected_pollutant} vs AQI",
            height=520, legend_title_text="AQI Category",
        )
        return apply_chart_theme(fig)

    @staticmethod
    def severe_contributors_bar(mean_df: pd.DataFrame) -> go.Figure:
        if mean_df.empty:
            return CorrelationCharts.empty_state(
                "Mean Pollutant Levels on Severe AQI Days",
                "No Severe AQI rows available.",
            )
        fig = px.bar(
            mean_df, x="Pollutant", y="Mean Value",
            text="Mean Value", color="Pollutant",
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")

        for pollutant, limit in WHO_LIMITS.items():
            if pollutant in mean_df["Pollutant"].values:
                fig.add_shape(
                    type="line", x0=-0.5, x1=len(mean_df) - 0.5,
                    y0=limit, y1=limit,
                    line=dict(color="#EF4444", dash="dash", width=1.5),
                )

        fig.update_layout(
            title="Mean Pollutant Levels on Severe AQI Days",
            height=440, showlegend=False,
        )
        return apply_chart_theme(fig)

    @staticmethod
    def bucket_boxplot(df: pd.DataFrame) -> go.Figure:
        if df.empty or COL_AQI_BUCKET not in df.columns:
            return CorrelationCharts.empty_state(
                "Pollutant Distribution Across AQI Buckets",
                "No AQI bucket data available.",
            )
        long_df = df[[COL_AQI_BUCKET, *POLLUTANT_COLUMNS]].melt(
            id_vars=COL_AQI_BUCKET,
            value_vars=POLLUTANT_COLUMNS,
            var_name="Pollutant", value_name="Value",
        )
        long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
        long_df = long_df.dropna(subset=[COL_AQI_BUCKET, "Value"])
        if long_df.empty:
            return CorrelationCharts.empty_state(
                "Pollutant Distribution Across AQI Buckets",
                "No pollutant values available.",
            )
        fig = px.box(
            long_df, x="Pollutant", y="Value",
            color=COL_AQI_BUCKET, points=False,
        )
        fig.update_layout(
            title="Pollutant Distribution Across AQI Buckets",
            height=500, legend_title_text="AQI Bucket",
        )
        return apply_chart_theme(fig)
