"""Charts ported from the former city_ranking.py and danger_frequency.py pages."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.charts import apply_chart_theme, empty_chart
from dashboard.config import (
    CHART_COLOR_SEQUENCE,
    CHART_DANGER_BUCKET_COLORS,
    CHART_RANK_CLEAN,
    CHART_RANK_CONTINUOUS_SCALE,
    CHART_RANK_POLLUTED,
    DANGEROUS_AQI_BUCKETS,
)
from dashboard.data.schema import COL_AQI, COL_AQI_BUCKET, COL_CITY, COL_DATE


class GeographyCharts:
    """City ranking + dangerous-day frequency charts (legacy page logic)."""

    # --- city_ranking.py -------------------------------------------------------

    @staticmethod
    def top_bottom_polluted_clean(df_rank: pd.DataFrame, top_n: int) -> go.Figure:
        if df_rank.empty:
            return empty_chart("Most Polluted vs Cleanest")
        worst = df_rank.head(top_n).copy()
        best = df_rank.tail(top_n).sort_values("aqi_mean", ascending=True).copy()
        worst["group"] = "Most polluted"
        best["group"] = "Cleanest"
        combined = pd.concat([worst, best], ignore_index=True)
        fig = px.bar(
            combined,
            y=COL_CITY,
            x="aqi_mean",
            color="group",
            orientation="h",
            color_discrete_map={
                "Most polluted": CHART_RANK_POLLUTED,
                "Cleanest": CHART_RANK_CLEAN,
            },
            text="aqi_mean",
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(
            title=f"Top {top_n} Most Polluted vs Cleanest Cities (Mean AQI)",
            xaxis_title="Mean AQI",
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
            return empty_chart("All Cities Ranked by Mean AQI")
        fig = px.bar(
            df_rank,
            x=COL_CITY,
            y="aqi_mean",
            color="aqi_mean",
            color_continuous_scale=CHART_RANK_CONTINUOUS_SCALE,
            text="aqi_mean",
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(
            title="All Cities Ranked by Mean AQI (highest → lowest)",
            xaxis_title="",
            yaxis_title="Mean AQI",
            height=520,
            coloraxis_colorbar_title="AQI",
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def aqi_box_by_cities(df: pd.DataFrame, cities: list[str]) -> go.Figure:
        sub = df.loc[(df[COL_CITY].isin(cities)) & (df[COL_AQI].notna())].copy()
        if sub.empty:
            return empty_chart("Daily AQI Distribution per City")
        fig = px.box(
            sub,
            x=COL_CITY,
            y=COL_AQI,
            color=COL_CITY,
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
            points=False,
        )
        fig.update_layout(
            title="Daily AQI Distribution per City",
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
            return empty_chart("Mean AQI by City × Year")
        t = df.copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t = t.dropna(subset=[COL_DATE, COL_AQI])
        t["year"] = t[COL_DATE].dt.year
        pivot = t.pivot_table(values=COL_AQI, index=COL_CITY, columns="year", aggfunc="mean")
        pivot = pivot.sort_values(by=pivot.columns.tolist(), ascending=False)
        fig = px.imshow(
            pivot,
            color_continuous_scale=CHART_RANK_CONTINUOUS_SCALE,
            text_auto=".0f",
            aspect="auto",
        )
        fig.update_layout(
            title="Mean AQI by City × Year",
            xaxis_title="Year",
            yaxis_title="",
            height=max(400, len(pivot) * 28),
            coloraxis_colorbar_title="AQI",
        )
        return apply_chart_theme(fig)

    # --- danger_frequency.py ---------------------------------------------------

    @staticmethod
    def stacked_dangerous_days_by_city(df: pd.DataFrame) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty:
            return empty_chart("Dangerous AQI Days by City")
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
        fig = px.bar(
            counts,
            x=COL_CITY,
            y="days",
            color=COL_AQI_BUCKET,
            color_discrete_map=CHART_DANGER_BUCKET_COLORS,
            category_orders={COL_CITY: city_order, COL_AQI_BUCKET: bucket_order},
            barmode="stack",
            text="days",
        )
        fig.update_traces(textposition="inside", texttemplate="%{text}")
        fig.update_layout(
            title="Dangerous AQI Days by City (Stacked: Poor / Very Poor / Severe)",
            xaxis_title="",
            yaxis_title="Number of Days",
            height=520,
            legend_title_text="AQI Bucket",
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def grouped_dangerous_days_by_city(df: pd.DataFrame, top_n: int) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty:
            return empty_chart("Dangerous Days by Bucket (Grouped)")
        counts = (
            sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
            .size()
            .rename(columns={"size": "days"})
        )
        city_totals = counts.groupby(COL_CITY)["days"].sum().sort_values(ascending=False)
        top_cities = city_totals.head(top_n).index.tolist()
        counts = counts[counts[COL_CITY].isin(top_cities)]
        bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in counts[COL_AQI_BUCKET].unique()]
        fig = px.bar(
            counts,
            x=COL_CITY,
            y="days",
            color=COL_AQI_BUCKET,
            color_discrete_map=CHART_DANGER_BUCKET_COLORS,
            barmode="group",
            category_orders={COL_CITY: top_cities, COL_AQI_BUCKET: bucket_order},
        )
        fig.update_layout(
            title=f"Top {top_n} Cities — Dangerous Days by Bucket (Grouped)",
            xaxis_title="",
            yaxis_title="Number of Days",
            height=500,
            legend_title_text="AQI Bucket",
        )
        fig.update_xaxes(tickangle=-45)
        return apply_chart_theme(fig)

    @staticmethod
    def dangerous_bucket_pct_bar(df: pd.DataFrame) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty:
            return empty_chart("Proportion of Dangerous Buckets")
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
        fig = px.bar(
            counts,
            y=COL_CITY,
            x="pct",
            color=COL_AQI_BUCKET,
            orientation="h",
            color_discrete_map=CHART_DANGER_BUCKET_COLORS,
            category_orders={COL_CITY: list(reversed(city_order)), COL_AQI_BUCKET: bucket_order},
            text="pct",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
        fig.update_layout(
            title="Proportion of Dangerous Buckets within Each City (%)",
            xaxis_title="Percentage of Dangerous Days",
            yaxis_title="",
            height=max(420, len(city_order) * 28),
            legend_title_text="AQI Bucket",
            barmode="stack",
        )
        return apply_chart_theme(fig)

    @staticmethod
    def dangerous_days_yearly_trend(df: pd.DataFrame) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty or COL_DATE not in sub.columns:
            return empty_chart("Dangerous Days Over Time")
        sub[COL_DATE] = pd.to_datetime(sub[COL_DATE], errors="coerce")
        sub = sub.dropna(subset=[COL_DATE])
        sub["year"] = sub[COL_DATE].dt.year
        yearly = (
            sub.groupby(["year", COL_AQI_BUCKET], as_index=False)
            .size()
            .rename(columns={"size": "days"})
        )
        bucket_order = [b for b in ("Poor", "Very Poor", "Severe") if b in yearly[COL_AQI_BUCKET].unique()]
        fig = px.line(
            yearly,
            x="year",
            y="days",
            color=COL_AQI_BUCKET,
            markers=True,
            color_discrete_map=CHART_DANGER_BUCKET_COLORS,
            category_orders={COL_AQI_BUCKET: bucket_order},
        )
        fig.update_layout(
            title="Dangerous Days Over Time (All Cities Combined)",
            xaxis_title="Year",
            yaxis_title="Number of Days",
            height=420,
            legend_title_text="AQI Bucket",
        )
        return apply_chart_theme(fig)

    @staticmethod
    def dangerous_city_bucket_heatmap(df: pd.DataFrame) -> go.Figure:
        sub = df[df[COL_AQI_BUCKET].isin(DANGEROUS_AQI_BUCKETS)].copy()
        if sub.empty:
            return empty_chart("Dangerous Days Heatmap")
        counts = (
            sub.groupby([COL_CITY, COL_AQI_BUCKET], as_index=False)
            .size()
            .rename(columns={"size": "days"})
        )
        pivot = counts.pivot_table(values="days", index=COL_CITY, columns=COL_AQI_BUCKET, fill_value=0)
        for b in ("Severe", "Very Poor", "Poor"):
            if b not in pivot.columns:
                pivot[b] = 0
        pivot = pivot[["Poor", "Very Poor", "Severe"]]
        pivot["_total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("_total", ascending=True).drop(columns="_total")
        fig = px.imshow(
            pivot,
            text_auto=True,
            color_continuous_scale="OrRd",
            aspect="auto",
        )
        fig.update_layout(
            title="Dangerous Days Heatmap (City × Bucket)",
            xaxis_title="AQI Bucket",
            yaxis_title="",
            height=max(420, len(pivot) * 28),
            coloraxis_colorbar_title="Days",
        )
        return apply_chart_theme(fig)
