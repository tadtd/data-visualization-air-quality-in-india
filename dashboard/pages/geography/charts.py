"""Charts for the Geography page (city ranking + danger frequency)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.charts import apply_chart_theme, empty_chart
from dashboard.config import (
    AQI_BUCKET_VI,
    DANGEROUS_AQI_BUCKETS,
    get_aqi_colors,
    get_chart_color_sequence,
    get_danger_bucket_colors,
    get_rank_clean,
    get_rank_continuous_scale,
    get_rank_polluted,
)
from dashboard.data.schema import COL_AQI, COL_AQI_BUCKET, COL_CITY, COL_DATE


class GeographyCharts:
    """City ranking + dangerous-day frequency charts."""

    @staticmethod
    def top_bottom_polluted_clean(df_rank: pd.DataFrame, top_n: int) -> go.Figure:
        if df_rank.empty:
            return empty_chart("Ô nhiễm nhất vs Sạch nhất")
        worst = df_rank.head(top_n).copy()
        best = df_rank.tail(top_n).sort_values("aqi_mean", ascending=True).copy()
        worst["group"] = "Ô nhiễm nhất"
        best["group"] = "Sạch nhất"
        combined = pd.concat([worst, best], ignore_index=True)
        fig = px.bar(
            combined,
            y=COL_CITY,
            x="aqi_mean",
            color="group",
            orientation="h",
            color_discrete_map={
                "Ô nhiễm nhất": get_rank_polluted(),
                "Sạch nhất": get_rank_clean(),
            },
            text="aqi_mean",
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(
            title=f"Top {top_n} thành phố ô nhiễm nhất vs sạch nhất (AQI trung bình)",
            xaxis_title="AQI trung bình",
            yaxis_title="",
            height=max(400, top_n * 38),
            legend_title_text="",
            yaxis=dict(categoryorder="total ascending"),
            margin=dict(l=10, r=60),
        )
        return apply_chart_theme(fig)

    @staticmethod
    def full_city_ranking_bar(df_rank: pd.DataFrame) -> go.Figure:
        if df_rank.empty:
            return empty_chart("Xếp hạng toàn bộ thành phố")
        fig = px.bar(
            df_rank,
            x=COL_CITY,
            y="aqi_mean",
            color="aqi_mean",
            color_continuous_scale=get_rank_continuous_scale(),
            text="aqi_mean",
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(
            title="Xếp hạng toàn bộ thành phố theo AQI (cao → thấp)",
            xaxis_title="",
            yaxis_title="AQI trung bình",
            height=520,
            coloraxis_colorbar_title="AQI",
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def aqi_box_by_cities(df: pd.DataFrame, cities: list[str]) -> go.Figure:
        sub = df.loc[(df[COL_CITY].isin(cities)) & (df[COL_AQI].notna())].copy()
        if sub.empty:
            return empty_chart("Phân bố AQI hàng ngày")
        fig = px.box(
            sub,
            x=COL_CITY,
            y=COL_AQI,
            color=COL_CITY,
            color_discrete_sequence=get_chart_color_sequence(),
            points=False,
        )
        fig.update_layout(
            title="Phân bố AQI hàng ngày theo thành phố",
            xaxis_title="",
            yaxis_title="AQI",
            height=480,
            showlegend=False,
        )
        fig.update_xaxes(tickangle=-35)
        return apply_chart_theme(fig)

    @staticmethod
    def yearly_mean_aqi_heatmap(df: pd.DataFrame) -> go.Figure:
        if df.empty or COL_DATE not in df.columns:
            return empty_chart("AQI trung bình theo Thành phố × Năm")
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE, COL_AQI])
        t["year"] = t[COL_DATE].dt.year
        pivot = t.pivot_table(values=COL_AQI, index=COL_CITY, columns="year", aggfunc="mean")
        pivot = pivot.sort_values(by=pivot.columns.tolist(), ascending=False)
        fig = px.imshow(
            pivot,
            color_continuous_scale=get_rank_continuous_scale(),
            text_auto=".0f",
            aspect="auto",
        )
        fig.update_layout(
            title="AQI trung bình theo Thành phố × Năm",
            xaxis_title="Năm",
            yaxis_title="",
            height=max(400, len(pivot) * 28),
            coloraxis_colorbar_title="AQI",
        )
        return apply_chart_theme(fig)

    # --- Danger frequency charts ---

    @staticmethod
    def stacked_dangerous_days_by_city(df: pd.DataFrame) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty:
            return empty_chart("Số ngày ô nhiễm nguy hiểm")
        counts = (
            sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
            .size()
            .rename(columns={"size": "days"})
        )
        bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in counts[COL_AQI_BUCKET].unique()]
        counts[COL_AQI_BUCKET] = pd.Categorical(counts[COL_AQI_BUCKET], categories=bucket_order, ordered=True)
        counts = counts.sort_values([COL_AQI_BUCKET, "days"], ascending=[True, False])
        city_totals = counts.groupby(COL_CITY)["days"].sum().sort_values(ascending=False)
        city_order = city_totals.index.tolist()

        danger_colors = get_danger_bucket_colors()
        # Vietnamese legend labels
        vi_labels = {b: AQI_BUCKET_VI.get(b, b) for b in bucket_order}
        counts["bucket_vi"] = counts[COL_AQI_BUCKET].map(vi_labels)

        fig = px.bar(
            counts,
            x=COL_CITY,
            y="days",
            color="bucket_vi",
            color_discrete_map={vi_labels.get(b, b): danger_colors.get(b, "#999") for b in bucket_order},
            category_orders={COL_CITY: city_order, "bucket_vi": [vi_labels[b] for b in bucket_order]},
            barmode="stack",
            text="days",
        )
        fig.update_traces(textposition="inside", texttemplate="%{text}")
        fig.update_layout(
            title="Số ngày ô nhiễm nguy hiểm theo thành phố (Kém / Rất kém / Nguy hiểm)",
            xaxis_title="",
            yaxis_title="Số ngày",
            height=520,
            legend_title_text="Mức AQI",
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def dangerous_bucket_pct_bar(df: pd.DataFrame) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty:
            return empty_chart("Tỉ lệ các mức nguy hiểm")
        counts = (
            sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
            .size()
            .rename(columns={"size": "days"})
        )
        totals = counts.groupby(COL_CITY)["days"].transform("sum")
        counts["pct"] = (counts["days"] / totals * 100).round(1)
        city_order = (
            counts.groupby(COL_CITY)["days"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )
        bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in counts[COL_AQI_BUCKET].unique()]

        danger_colors = get_danger_bucket_colors()
        vi_labels = {b: AQI_BUCKET_VI.get(b, b) for b in bucket_order}
        counts["bucket_vi"] = counts[COL_AQI_BUCKET].map(vi_labels)

        fig = px.bar(
            counts,
            y=COL_CITY,
            x="pct",
            color="bucket_vi",
            orientation="h",
            color_discrete_map={vi_labels.get(b, b): danger_colors.get(b, "#999") for b in bucket_order},
            category_orders={COL_CITY: list(reversed(city_order)), "bucket_vi": [vi_labels[b] for b in bucket_order]},
            text="pct",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
        fig.update_layout(
            title="Tỉ lệ các mức nguy hiểm trong mỗi thành phố (%)",
            xaxis_title="Phần trăm ngày nguy hiểm",
            yaxis_title="",
            height=max(420, len(city_order) * 28),
            legend_title_text="Mức AQI",
            barmode="stack",
        )
        return apply_chart_theme(fig)

    @staticmethod
    def dangerous_days_yearly_trend(df: pd.DataFrame) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty or COL_DATE not in sub.columns:
            return empty_chart("Xu hướng ngày nguy hiểm theo năm")
        sub[COL_DATE] = pd.to_datetime(sub[COL_DATE], errors="coerce")
        sub = sub.dropna(subset=[COL_DATE])
        sub["year"] = sub[COL_DATE].dt.year
        yearly = (
            sub.groupby(["year", COL_AQI_BUCKET], as_index=False)
            .size()
            .rename(columns={"size": "days"})
        )
        bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in yearly[COL_AQI_BUCKET].unique()]

        danger_colors = get_danger_bucket_colors()
        vi_labels = {b: AQI_BUCKET_VI.get(b, b) for b in bucket_order}
        yearly["bucket_vi"] = yearly[COL_AQI_BUCKET].map(vi_labels)

        fig = px.line(
            yearly,
            x="year",
            y="days",
            color="bucket_vi",
            markers=True,
            color_discrete_map={vi_labels.get(b, b): danger_colors.get(b, "#999") for b in bucket_order},
            category_orders={"bucket_vi": [vi_labels[b] for b in bucket_order]},
        )
        fig.update_layout(
            title="Xu hướng số ngày nguy hiểm theo năm (toàn quốc)",
            xaxis_title="Năm",
            yaxis_title="Số ngày",
            height=420,
            legend_title_text="Mức AQI",
        )
        return apply_chart_theme(fig)
