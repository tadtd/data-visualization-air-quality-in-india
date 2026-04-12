"""Insights page chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.components.charts import apply_chart_theme, empty_chart
from dashboard.config import CHART_COLOR_SEQUENCE


class InsightsCharts:
    """Chart builders for the Insights page."""

    @staticmethod
    def hotspot_duration_stacked(df: pd.DataFrame, *, threshold: int = 200) -> go.Figure:
        if df.empty:
            return empty_chart(f"Hotspot Episode Duration (AQI >= {threshold})")
        city_order = (
            df[["City", "avg_duration_days"]]
            .drop_duplicates()
            .sort_values("avg_duration_days", ascending=False)["City"]
            .tolist()
        )
        fig = px.bar(
            df, x="City", y="episodes", color="duration_group",
            category_orders={
                "City": city_order,
                "duration_group": ["Short (<=3d)", "Medium (4-7d)", "Long (>=8d)"],
            },
            color_discrete_map={
                "Short (<=3d)": CHART_COLOR_SEQUENCE[2],
                "Medium (4-7d)": CHART_COLOR_SEQUENCE[1],
                "Long (>=8d)": "#D62728",
            },
            custom_data=["avg_duration_days", "longest_duration_days", "total_episodes"],
        )
        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Group: %{fullData.name}<br>"
                "Episodes: %{y}<br>"
                "Avg duration: %{customdata[0]:.1f}d<br>"
                "Longest: %{customdata[1]}d<br>"
                "Total: %{customdata[2]}<extra></extra>"
            )
        )
        fig.update_layout(
            title=f"Hotspot Episodes: Short-term or Persistent? (AQI >= {threshold})",
            height=430, barmode="stack",
            legend_title_text="Duration",
        )
        fig.update_xaxes(tickangle=-30)
        return apply_chart_theme(fig)

    @staticmethod
    def hotspot_persistence(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Hotspot Pollution Persistence")
        sub = df.sort_values("longest_duration_days", ascending=False)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(
                x=sub["City"], y=sub["longest_duration_days"],
                name="Longest episode (days)",
                marker_color=CHART_COLOR_SEQUENCE[0],
                customdata=sub[["avg_duration_days", "total_episodes"]].values,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Longest: %{y}d<br>"
                    "Avg: %{customdata[0]:.1f}d<br>"
                    "Total episodes: %{customdata[1]}<extra></extra>"
                ),
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=sub["City"], y=sub["long_episode_ratio"] * 100,
                mode="lines+markers",
                name="Long episodes >=8d (%)",
                line=dict(color="#D62728", width=2),
                marker=dict(size=7),
                hovertemplate="<b>%{x}</b><br>Long ratio: %{y:.1f}%<extra></extra>",
            ),
            secondary_y=True,
        )
        fig.update_layout(
            title="Pollution Persistence at Hotspot Cities",
            height=430,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(tickangle=-30)
        fig.update_yaxes(title_text="Days", secondary_y=False)
        fig.update_yaxes(title_text="Ratio (%)", secondary_y=True)
        return apply_chart_theme(fig)

    @staticmethod
    def metro_priority_bar(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Pollutant Control Priority Ranking")
        sub = df.sort_values("priority_score", ascending=False)
        fig = px.bar(
            sub, x="pollutant", y="priority_score",
            color="mean_abs_corr", color_continuous_scale="YlOrRd",
            custom_data=["mean_abs_corr", "mean_severe_lift", "n_cities"],
        )
        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Priority: %{y:.3f}<br>"
                "|AQI corr|: %{customdata[0]:.3f}<br>"
                "Severe uplift: %{customdata[1]:.2f}x<br>"
                "Cities: %{customdata[2]}<extra></extra>"
            )
        )
        fig.update_layout(
            title="Pollutant Control Priority Ranking (Major Cities)",
            height=420, coloraxis_colorbar_title="|corr|",
        )
        return apply_chart_theme(fig)

    @staticmethod
    def metro_priority_heatmap(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Priority Heatmap by City × Pollutant")
        pivot = df.pivot_table(index="City", columns="pollutant", values="priority_score", aggfunc="mean")
        if pivot.empty:
            return empty_chart("Priority Heatmap by City × Pollutant")
        city_order = df.groupby("City")["priority_score"].mean().sort_values(ascending=False).index.tolist()
        pollutant_order = (
            df.groupby("pollutant")["priority_score"].mean()
            .sort_values(ascending=False).index.tolist()
        )
        pivot = pivot.reindex(index=city_order, columns=pollutant_order)
        fig = px.imshow(
            pivot, color_continuous_scale="YlOrRd",
            zmin=0, zmax=1, aspect="auto",
            labels={"x": "Pollutant", "y": "City", "color": "Priority"},
            text_auto=".2f",
        )
        fig.update_layout(
            title="Control Priority Heatmap by City",
            height=max(360, 36 * len(pivot.index) + 120),
        )
        fig.update_xaxes(tickangle=-30)
        return apply_chart_theme(fig)
