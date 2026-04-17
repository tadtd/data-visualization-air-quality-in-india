"""Temporal page chart builders."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.components.charts import add_aqi_reference_lines, apply_chart_theme, empty_chart
from dashboard.config import get_chart_color_sequence


class TemporalCharts:
    """Chart builders for the Temporal page."""

    @staticmethod
    def yearly_line(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("AQI trung bình theo năm (2015–2020)")
        colors = get_chart_color_sequence()
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=pd.concat([df["year"], df["year"].iloc[::-1]]).tolist(),
                y=pd.concat([df["aqi_mean"] + df["aqi_std"], (df["aqi_mean"] - df["aqi_std"]).iloc[::-1]]).tolist(),
                fill="toself",
                fillcolor="rgba(1,115,178,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="±1 Độ lệch chuẩn",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=df["aqi_mean"],
                mode="lines+markers",
                line=dict(color=colors[0], width=2),
                marker=dict(size=8),
                name="AQI trung bình",
            )
        )
        add_aqi_reference_lines(fig)
        if 2020 in df["year"].values:
            fig.add_vline(x=2020, line_dash="dot", line_color="grey", line_width=1)
            fig.add_annotation(
                x=2020, y=1, yref="paper", text="COVID-19",
                showarrow=False, font=dict(size=10, color="grey"),
                xanchor="left", yanchor="top",
            )
        fig.update_layout(
            title="AQI trung bình theo năm (2015–2020)",
            xaxis_title="Năm",
            yaxis_title="AQI",
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(dtick=1)
        return apply_chart_theme(fig)

    @staticmethod
    def monthly_line(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("AQI toàn quốc theo tháng")
        colors = get_chart_color_sequence()
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["year_month"], y=df["aqi_mean"],
                mode="lines", fill="tozeroy",
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
            title="AQI toàn quốc theo tháng",
            xaxis_title="Tháng",
            yaxis_title="AQI",
            height=400,
        )
        fig.update_xaxes(tickangle=-45, nticks=12)
        return apply_chart_theme(fig)

    @staticmethod
    def city_small_multiples(df: pd.DataFrame, *, ncols: int = 2) -> go.Figure:
        if df.empty:
            return empty_chart("AQI theo tháng — từng thành phố")
        colors = get_chart_color_sequence()
        cities = (
            df.groupby("City")["aqi_mean"]
            .mean()
            .sort_values(ascending=False)
            .index.tolist()
        )
        nrows = -(-len(cities) // ncols)
        fig = make_subplots(
            rows=nrows, cols=ncols,
            shared_xaxes=False, shared_yaxes=True,
            subplot_titles=cities,
            vertical_spacing=0.12, horizontal_spacing=0.08,
        )
        y_max = df["aqi_mean"].max() * 1.1
        for i, city in enumerate(cities):
            row, col = divmod(i, ncols)
            city_df = df[df["City"] == city].sort_values("year_month").reset_index(drop=True)
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=city_df["year_month"], y=city_df["aqi_mean"],
                    mode="lines", line=dict(color=color, width=2),
                    name=city, showlegend=False,
                ),
                row=row + 1, col=col + 1,
            )
            if len(city_df) >= 2:
                t_vals = np.arange(len(city_df), dtype=float)
                y_vals = city_df["aqi_mean"].to_numpy(dtype=float)
                valid = ~np.isnan(y_vals)
                if valid.sum() >= 2:
                    coeffs = np.polyfit(t_vals[valid], y_vals[valid], 1)
                    trend_y = np.polyval(coeffs, t_vals).tolist()
                    fig.add_trace(
                        go.Scatter(
                            x=city_df["year_month"].tolist(), y=trend_y,
                            mode="lines", line=dict(color="black", dash="dash", width=1.5),
                            name="Xu hướng", showlegend=False,
                        ),
                        row=row + 1, col=col + 1,
                    )
            axis_n = "" if i == 0 else str(i + 1)
            fig.add_shape(
                type="line", x0=0, x1=1, xref=f"x{axis_n} domain",
                y0=100, y1=100, yref=f"y{axis_n}",
                line=dict(color="grey", dash="dash", width=1),
            )
        fig.update_yaxes(range=[0, y_max])
        fig.update_xaxes(tickangle=-45, nticks=6)
        fig.update_layout(
            title="AQI theo tháng — Top 6 thành phố ô nhiễm nhất",
            height=220 * nrows + 80,
            margin=dict(t=60, b=40, l=40, r=20),
        )
        return apply_chart_theme(fig)

    @staticmethod
    def seasonal_profile(df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return empty_chart("Biểu đồ mùa vụ AQI")
        colors = get_chart_color_sequence()
        color_winter = colors[1]
        color_nonwinter = colors[0]

        def std_array(mask: pd.Series) -> list:
            return [value if pd.notna(value) else None for value in df.loc[mask, "aqi_std"]]

        winter_mask = df["is_winter"]
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df.loc[~winter_mask, "month_name"],
                y=df.loc[~winter_mask, "aqi_mean"],
                error_y=dict(type="data", array=std_array(~winter_mask), visible=True),
                marker_color=color_nonwinter, name="Ngoài mùa đông",
            )
        )
        fig.add_trace(
            go.Bar(
                x=df.loc[winter_mask, "month_name"],
                y=df.loc[winter_mask, "aqi_mean"],
                error_y=dict(type="data", array=std_array(winter_mask), visible=True),
                marker_color=color_winter, name="Mùa đông (T11–T2)",
            )
        )
        fig.update_layout(
            title="Biểu đồ AQI theo tháng trong năm (mùa vụ)",
            xaxis_title="Tháng",
            yaxis_title="AQI trung bình",
            height=400, barmode="group",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(categoryorder="array", categoryarray=df["month_name"].tolist()),
        )
        return apply_chart_theme(fig)

    @staticmethod
    def trend_slope_bar(df: pd.DataFrame, *, top_n: int = 15) -> go.Figure:
        if df.empty:
            return empty_chart("Xu hướng AQI theo thành phố")
        colors = get_chart_color_sequence()
        improving = df[df["trend_label"] == "Improving"].sort_values("slope").head(top_n)
        stable = df[df["trend_label"] == "Stable"]
        worsening = df[df["trend_label"] == "Worsening"].sort_values("slope", ascending=False).head(top_n)
        sub = pd.concat([improving, stable, worsening]).drop_duplicates().sort_values("slope")
        fig = go.Figure()
        for label, vi_label, color in [
            ("Improving", "Cải thiện", colors[2]),
            ("Stable", "Ổn định", colors[5]),
            ("Worsening", "Xấu đi", "#D62728"),
        ]:
            group = sub[sub["trend_label"] == label]
            if group.empty:
                continue
            fig.add_trace(
                go.Bar(
                    y=group["City"], x=group["slope"],
                    orientation="h", marker_color=color, name=vi_label,
                    customdata=group[["r_squared", "n_months"]].values,
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Độ dốc: %{x:.3f} AQI/tháng<br>"
                        "R²: %{customdata[0]:.2f}<br>"
                        "Số tháng: %{customdata[1]}<extra></extra>"
                    ),
                )
            )
        fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=1)
        fig.update_layout(
            title="Xu hướng AQI theo thành phố (âm = cải thiện, dương = xấu đi)",
            xaxis_title="Độ dốc (AQI/tháng)",
            yaxis_title="",
            height=max(380, 28 * len(sub) + 100),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=140, r=20, t=60, b=40),
            barmode="relative",
        )
        return apply_chart_theme(fig)

    @staticmethod
    def year_on_year(df: pd.DataFrame) -> go.Figure:
        """One line per year overlaid on a 12-month x-axis."""
        if df.empty:
            return empty_chart("So sánh AQI qua các năm")
        colors = get_chart_color_sequence()
        fig = go.Figure()
        years = sorted(df["year"].unique())
        n = len(years)
        for i, year in enumerate(years):
            yr_df = df[df["year"] == year].sort_values("month")
            shade = max(0.3, 1.0 - (n - 1 - i) * 0.15)
            fig.add_trace(
                go.Scatter(
                    x=yr_df["month_name"], y=yr_df["aqi_mean"],
                    mode="lines+markers",
                    line=dict(color=colors[0], width=2),
                    opacity=shade,
                    marker=dict(size=5),
                    name=str(int(year)),
                )
            )
        fig.update_layout(
            title="So sánh AQI qua các năm",
            xaxis_title="Tháng",
            yaxis_title="AQI trung bình",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return apply_chart_theme(fig)

    @staticmethod
    def aqi_breach(df: pd.DataFrame, *, threshold: int = 200) -> go.Figure:
        if df.empty:
            return empty_chart(f"Số ngày AQI > {threshold} theo năm")
        colors = get_chart_color_sequence()
        fig = px.bar(
            df, x="year", y="breach_days",
            color_discrete_sequence=[colors[1]],
        )
        fig.update_layout(
            title=f"Số ngày AQI vượt {threshold} theo năm",
            xaxis_title="Năm",
            yaxis_title="Số ngày",
            height=360,
        )
        fig.update_xaxes(dtick=1)
        return apply_chart_theme(fig)
