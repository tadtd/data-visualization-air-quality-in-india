"""Insights page chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.components.charts import apply_chart_theme, empty_chart
from dashboard.config import get_chart_color_sequence


class InsightsCharts:
    """Chart builders for the Insights page."""

    @staticmethod
    def hotspot_duration_stacked(df: pd.DataFrame, *, threshold: int = 200) -> go.Figure:
        if df.empty:
            return empty_chart(f"Thời lượng đợt ô nhiễm (AQI ≥ {threshold})")
        colors = get_chart_color_sequence()
        city_order = (
            df[["City", "avg_duration_days"]]
            .drop_duplicates()
            .sort_values("avg_duration_days", ascending=False)["City"]
            .tolist()
        )
        # Vietnamese duration labels
        vi_duration = {
            "Short (<=3d)": "Ngắn (≤3 ngày)",
            "Medium (4-7d)": "Trung bình (4–7 ngày)",
            "Long (>=8d)": "Dài (≥8 ngày)",
        }
        df = df.copy()
        df["duration_vi"] = df["duration_group"].map(lambda g: vi_duration.get(g, g))

        fig = px.bar(
            df, x="City", y="episodes", color="duration_vi",
            category_orders={
                "City": city_order,
                "duration_vi": list(vi_duration.values()),
            },
            color_discrete_map={
                "Ngắn (≤3 ngày)": colors[2],
                "Trung bình (4–7 ngày)": colors[1],
                "Dài (≥8 ngày)": "#D62728",
            },
            custom_data=["avg_duration_days", "longest_duration_days", "total_episodes"],
        )
        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Nhóm: %{fullData.name}<br>"
                "Số đợt: %{y}<br>"
                "TB: %{customdata[0]:.1f} ngày<br>"
                "Dài nhất: %{customdata[1]} ngày<br>"
                "Tổng: %{customdata[2]}<extra></extra>"
            )
        )
        fig.update_layout(
            title=f"Các đợt ô nhiễm: ngắn hạn hay dai dẳng? (AQI ≥ {threshold})",
            height=430, barmode="stack",
            legend_title_text="Thời lượng",
        )
        fig.update_xaxes(tickangle=-30)
        return apply_chart_theme(fig)

    @staticmethod
    def hotspot_persistence(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Mức độ dai dẳng của ô nhiễm")
        colors = get_chart_color_sequence()
        sub = df.sort_values("longest_duration_days", ascending=False)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(
                x=sub["City"], y=sub["longest_duration_days"],
                name="Đợt dài nhất (ngày)",
                marker_color=colors[0],
                customdata=sub[["avg_duration_days", "total_episodes"]].values,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Dài nhất: %{y} ngày<br>"
                    "TB: %{customdata[0]:.1f} ngày<br>"
                    "Tổng đợt: %{customdata[1]}<extra></extra>"
                ),
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=sub["City"], y=sub["long_episode_ratio"] * 100,
                mode="lines+markers",
                name="Tỉ lệ đợt dài ≥8 ngày (%)",
                line=dict(color="#D62728", width=2),
                marker=dict(size=7),
                hovertemplate="<b>%{x}</b><br>Tỉ lệ dài: %{y:.1f}%<extra></extra>",
            ),
            secondary_y=True,
        )
        fig.update_layout(
            title="Mức độ dai dẳng của ô nhiễm tại các điểm nóng",
            height=430,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(tickangle=-30)
        fig.update_yaxes(title_text="Ngày", secondary_y=False)
        fig.update_yaxes(title_text="Tỉ lệ (%)", secondary_y=True)
        return apply_chart_theme(fig)

    @staticmethod
    def metro_priority_bar(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Xếp hạng ưu tiên kiểm soát chất ô nhiễm")
        sub = df.sort_values("priority_score", ascending=False)
        fig = px.bar(
            sub, x="pollutant", y="priority_score",
            color="mean_abs_corr", color_continuous_scale="YlOrRd",
            custom_data=["mean_abs_corr", "mean_severe_lift", "n_cities"],
        )
        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Điểm ưu tiên: %{y:.3f}<br>"
                "|Tương quan AQI|: %{customdata[0]:.3f}<br>"
                "Mức tăng khi nguy hiểm: %{customdata[1]:.2f}x<br>"
                "Số thành phố: %{customdata[2]}<extra></extra>"
            )
        )
        fig.update_layout(
            title="Xếp hạng ưu tiên kiểm soát chất ô nhiễm (các thành phố lớn)",
            xaxis_title="Chất ô nhiễm",
            yaxis_title="Điểm ưu tiên",
            height=420, coloraxis_colorbar_title="|Tương quan|",
        )
        return apply_chart_theme(fig)

    @staticmethod
    def metro_priority_heatmap(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Heatmap ưu tiên theo Thành phố × Chất ô nhiễm")
        pivot = df.pivot_table(index="City", columns="pollutant", values="priority_score", aggfunc="mean")
        if pivot.empty:
            return empty_chart("Heatmap ưu tiên theo Thành phố × Chất ô nhiễm")
        city_order = df.groupby("City")["priority_score"].mean().sort_values(ascending=False).index.tolist()
        pollutant_order = (
            df.groupby("pollutant")["priority_score"].mean()
            .sort_values(ascending=False).index.tolist()
        )
        pivot = pivot.reindex(index=city_order, columns=pollutant_order)
        fig = px.imshow(
            pivot, color_continuous_scale="YlOrRd",
            zmin=0, zmax=1, aspect="auto",
            labels={"x": "Chất ô nhiễm", "y": "Thành phố", "color": "Ưu tiên"},
            text_auto=".2f",
        )
        fig.update_layout(
            title="Heatmap mức ưu tiên kiểm soát theo thành phố",
            height=max(360, 36 * len(pivot.index) + 120),
        )
        fig.update_xaxes(tickangle=-30)
        return apply_chart_theme(fig)
