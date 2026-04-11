"""Plotly chart factories (placeholders / simple views)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from dashboard.config import CHART_COLOR_SEQUENCE, DANGEROUS_AQI_BUCKETS


def line_placeholder(title: str = "Trend") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text="Chart placeholder — connect data in transforms",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
    )
    fig.update_layout(title=title, height=360, margin=dict(t=40, b=40))
    return fig


def monthly_aqi_line(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return line_placeholder("AQI trung bình theo tháng (toàn quốc)")
    fig = px.line(
        df,
        x="year_month",
        y="aqi_mean",
        markers=False,
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
    )
    fig.add_hline(
        y=100, line_dash="dash", line_color="orange", line_width=1.5,
        annotation_text="Trung bình (100)", annotation_position="top left",
    )
    fig.add_hline(
        y=200, line_dash="dash", line_color="red", line_width=1.5,
        annotation_text="Kém (200)", annotation_position="top left",
    )
    # COVID-19 lockdown annotation
    if "2020-03" in df["year_month"].values:
        fig.add_vline(
            x="2020-03", line_dash="dot", line_color="grey", line_width=1,
        )
        fig.add_annotation(
            x="2020-03", y=1, yref="paper",
            text="COVID-19", showarrow=False,
            font=dict(size=10, color="grey"),
            xanchor="left", yanchor="top",
        )
    fig.update_layout(
        title="AQI trung bình theo tháng (toàn quốc)",
        xaxis_title="Tháng",
        yaxis_title="AQI trung bình",
        height=400,
    )
    fig.update_xaxes(tickangle=-45, nticks=12)
    return fig


def city_bar_top_bottom(df: pd.DataFrame, *, top_n: int = 10) -> go.Figure:
    if df.empty:
        return line_placeholder("City mean AQI")
    top = df.head(top_n)
    bottom = df.tail(top_n).sort_values("aqi_mean", ascending=True)
    sub = pd.concat([top, bottom], ignore_index=True)
    sub["_group"] = ["Top"] * len(top) + ["Bottom"] * len(bottom)
    fig = px.bar(
        sub,
        x="City",
        y="aqi_mean",
        color="_group",
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
    )
    fig.update_layout(
        title=f"Top / bottom {top_n} cities by mean AQI",
        xaxis_title="City",
        yaxis_title="Mean AQI",
        height=450,
        showlegend=True,
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def dangerous_days_bar(df: pd.DataFrame, *, top_n: int = 15) -> go.Figure:
    if df.empty:
        return line_placeholder("Dangerous-day counts")
    sub = df.head(top_n)
    fig = px.bar(
        sub,
        x="City",
        y="danger_days",
        color_discrete_sequence=[CHART_COLOR_SEQUENCE[0]],
    )
    fig.update_layout(
        title=f"Days in {', '.join(sorted(DANGEROUS_AQI_BUCKETS))} (top {top_n})",
        xaxis_title="City",
        yaxis_title="Day count",
        height=450,
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def correlation_heatmap(df: pd.DataFrame, cols: list[str]) -> go.Figure:
    """Pearson correlation heatmap for numeric columns present in df."""
    use = [c for c in cols if c in df.columns]
    if len(use) < 2:
        return line_placeholder("Correlation heatmap")
    num = df[use].apply(pd.to_numeric, errors="coerce")
    corr = num.corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(title="Pollutant / AQI correlation (Pearson)", height=520)
    return fig


def show_chart(fig: go.Figure, *, use_container_width: bool = True) -> None:
    width_mode = "stretch" if use_container_width else "content"
    st.plotly_chart(fig, width=width_mode)


# ---------------------------------------------------------------------------
# Temporal trend charts
# ---------------------------------------------------------------------------

def yearly_aqi_line(df: pd.DataFrame) -> go.Figure:
    """Annual mean AQI line with ±1 std deviation shaded band."""
    if df.empty:
        return line_placeholder("AQI trung bình theo năm (2015–2020)")
    fig = go.Figure()
    # Upper and lower std bounds (shaded area)
    fig.add_trace(go.Scatter(
        x=pd.concat([df["year"], df["year"].iloc[::-1]]).tolist(),
        y=pd.concat([df["aqi_mean"] + df["aqi_std"], (df["aqi_mean"] - df["aqi_std"]).iloc[::-1]]).tolist(),
        fill="toself",
        fillcolor="rgba(1,115,178,0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="±1 độ lệch chuẩn",
        hoverinfo="skip",
    ))
    # Mean line
    fig.add_trace(go.Scatter(
        x=df["year"],
        y=df["aqi_mean"],
        mode="lines+markers",
        line=dict(color=CHART_COLOR_SEQUENCE[0], width=2),
        marker=dict(size=8),
        name="AQI trung bình",
    ))
    # Threshold lines
    fig.add_hline(
        y=100, line_dash="dash", line_color="orange", line_width=1.5,
        annotation_text="Trung bình (100)", annotation_position="top left",
    )
    fig.add_hline(
        y=200, line_dash="dash", line_color="red", line_width=1.5,
        annotation_text="Kém (200)", annotation_position="top left",
    )
    # COVID-19 2020 annotation
    if 2020 in df["year"].values:
        fig.add_vline(x=2020, line_dash="dot", line_color="grey", line_width=1)
        fig.add_annotation(
            x=2020, y=1, yref="paper",
            text="COVID-19", showarrow=False,
            font=dict(size=10, color="grey"),
            xanchor="left", yanchor="top",
        )
    fig.update_layout(
        title="AQI trung bình theo năm (2015–2020)",
        xaxis_title="Năm",
        yaxis_title="AQI trung bình",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(dtick=1)
    return fig


def city_small_multiples_line(df: pd.DataFrame, *, ncols: int = 2) -> go.Figure:
    """Small-multiples line chart: one subplot per city, shared y-axis range."""
    if df.empty:
        return line_placeholder("Monthly AQI by city")

    # Sort cities by overall mean AQI descending so the most-polluted city
    # always appears top-left and the grid order is deterministic.
    cities = (
        df.groupby("City")["aqi_mean"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    nrows = -(-len(cities) // ncols)  # ceiling division

    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        shared_xaxes=False,
        shared_yaxes=True,
        subplot_titles=cities,
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    y_max = df["aqi_mean"].max() * 1.1

    for i, city in enumerate(cities):
        row, col = divmod(i, ncols)
        city_df = df[df["City"] == city].sort_values("year_month").reset_index(drop=True)
        color = CHART_COLOR_SEQUENCE[i % len(CHART_COLOR_SEQUENCE)]
        fig.add_trace(
            go.Scatter(
                x=city_df["year_month"],
                y=city_df["aqi_mean"],
                mode="lines",
                line=dict(color=color, width=2),
                name=city,
                showlegend=False,
            ),
            row=row + 1,
            col=col + 1,
        )
        # Regression trend line
        if len(city_df) >= 2:
            t_vals = np.arange(len(city_df), dtype=float)
            y_vals = city_df["aqi_mean"].to_numpy(dtype=float)
            valid = ~np.isnan(y_vals)
            if valid.sum() >= 2:
                coeffs = np.polyfit(t_vals[valid], y_vals[valid], 1)
                trend_y = np.polyval(coeffs, t_vals).tolist()
                fig.add_trace(
                    go.Scatter(
                        x=city_df["year_month"].tolist(),
                        y=trend_y,
                        mode="lines",
                        line=dict(color="black", dash="dash", width=1.5),
                        name="Xu hướng",
                        showlegend=False,
                    ),
                    row=row + 1,
                    col=col + 1,
                )
        # AQI = 100 reference line per subplot
        # Plotly axis refs: subplot 1 → "x"/"y", subplot N>1 → "xN"/"yN"
        axis_n = "" if i == 0 else str(i + 1)
        fig.add_shape(
            type="line",
            x0=0, x1=1, xref=f"x{axis_n} domain",
            y0=100, y1=100, yref=f"y{axis_n}",
            line=dict(color="grey", dash="dash", width=1),
        )

    fig.update_yaxes(range=[0, y_max])
    fig.update_xaxes(tickangle=-45, nticks=6)
    fig.update_layout(
        title="AQI trung bình theo tháng — top 6 thành phố ô nhiễm nhất",
        height=220 * nrows + 80,
        margin=dict(t=60, b=40, l=40, r=20),
    )
    return fig


def multi_city_trend_line(df: pd.DataFrame) -> go.Figure:
    """Monthly mean AQI overlaid for multiple cities."""
    if df.empty:
        return line_placeholder("Monthly AQI by city")
    fig = px.line(
        df,
        x="year_month",
        y="aqi_mean",
        color="City",
        markers=False,
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
    )
    # AQI = 100 reference line (boundary between Satisfactory and Moderate)
    fig.add_hline(y=100, line_dash="dash", line_color="grey", annotation_text="AQI 100", annotation_position="top left")
    fig.update_layout(
        title="Monthly mean AQI by city",
        xaxis_title="Month",
        yaxis_title="Mean AQI",
        height=460,
        legend_title_text="City",
    )
    fig.update_xaxes(tickangle=-45, nticks=20)
    return fig


def seasonal_profile_bar(df: pd.DataFrame) -> go.Figure:
    """Monthly AQI profile (Jan–Dec) with error bars — highlights winter peaks."""
    if df.empty:
        return line_placeholder("Seasonal AQI profile")

    # Separate winter and non-winter rows for two named traces so Plotly
    # produces a proper legend instead of a fragile HTML annotation.
    color_winter = CHART_COLOR_SEQUENCE[1]
    color_nonwinter = CHART_COLOR_SEQUENCE[0]

    # None suppresses the error bar for months missing std (e.g. single observation).
    def _std_array(mask: pd.Series) -> list:
        return [v if pd.notna(v) else None for v in df.loc[mask, "aqi_std"]]

    winter_mask = df["is_winter"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df.loc[~winter_mask, "month_name"],
        y=df.loc[~winter_mask, "aqi_mean"],
        error_y=dict(type="data", array=_std_array(~winter_mask), visible=True),
        marker_color=color_nonwinter,
        name="Non-Winter",
    ))
    fig.add_trace(go.Bar(
        x=df.loc[winter_mask, "month_name"],
        y=df.loc[winter_mask, "aqi_mean"],
        error_y=dict(type="data", array=_std_array(winter_mask), visible=True),
        marker_color=color_winter,
        name="Winter (Nov–Feb)",
    ))
    fig.update_layout(
        title="AQI trung bình theo tháng lịch (hồ sơ mùa vụ)",
        xaxis_title="Tháng",
        yaxis_title="AQI trung bình",
        height=400,
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(categoryorder="array", categoryarray=df["month_name"].tolist()),
    )
    return fig


def city_trend_slope_bar(df: pd.DataFrame, *, top_n: int = 15) -> go.Figure:
    """Horizontal diverging bar chart of per-city AQI trend slopes (AQI units/month).

    Horizontal orientation keeps city labels readable regardless of city count.
    Shows the top_n most improving and top_n most worsening cities plus all stable cities.
    """
    if df.empty:
        return line_placeholder("Xu hướng AQI theo thành phố")

    improving = df[df["trend_label"] == "Improving"].sort_values("slope").head(top_n)
    stable = df[df["trend_label"] == "Stable"]
    worsening = df[df["trend_label"] == "Worsening"].sort_values("slope", ascending=False).head(top_n)
    sub = pd.concat([improving, stable, worsening]).drop_duplicates().sort_values("slope")

    fig = go.Figure()

    for label, color, vn_label in [
        ("Improving", CHART_COLOR_SEQUENCE[2], "Cải thiện"),
        ("Stable", CHART_COLOR_SEQUENCE[5], "Ổn định"),
        ("Worsening", "#D62728", "Xấu đi"),
    ]:
        grp = sub[sub["trend_label"] == label]
        if grp.empty:
            continue
        fig.add_trace(go.Bar(
            y=grp["City"],
            x=grp["slope"],
            orientation="h",
            marker_color=color,
            name=vn_label,
            customdata=grp[["r_squared", "n_months"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Hệ số xu hướng: %{x:.3f} AQI/tháng<br>"
                "R²: %{customdata[0]:.2f}<br>"
                "Số tháng: %{customdata[1]}<extra></extra>"
            ),
        ))

    fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=1)
    fig.update_layout(
        title="Xu hướng AQI theo thành phố (âm = cải thiện, dương = xấu đi)",
        xaxis_title="Hệ số xu hướng (AQI/tháng)",
        yaxis_title=None,
        height=max(380, 28 * len(sub) + 100),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=140, r=20, t=60, b=40),
        barmode="relative",
    )
    return fig


def aqi_breach_bar(df: pd.DataFrame, *, threshold: int = 200) -> go.Figure:
    """Bar chart of days per year where AQI exceeds the threshold."""
    if df.empty:
        return line_placeholder(f"Số ngày AQI vượt ngưỡng {threshold}")
    fig = px.bar(
        df,
        x="year",
        y="breach_days",
        color_discrete_sequence=[CHART_COLOR_SEQUENCE[1]],
    )
    fig.update_layout(
        title=f"Số ngày AQI vượt ngưỡng {threshold} theo năm",
        xaxis_title="Năm",
        yaxis_title="Số ngày",
        height=360,
    )
    fig.update_xaxes(dtick=1)
    return fig


def hotspot_duration_stacked_bar(df: pd.DataFrame, *, threshold: int = 200) -> go.Figure:
    """Stacked bar of hotspot episode counts by duration band for each city."""
    if df.empty:
        return line_placeholder(f"Phân bố độ dài đợt ô nhiễm (AQI >= {threshold})")

    city_order = (
        df[["City", "avg_duration_days"]]
        .drop_duplicates()
        .sort_values("avg_duration_days", ascending=False)["City"]
        .tolist()
    )
    fig = px.bar(
        df,
        x="City",
        y="episodes",
        color="duration_group",
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
            "Nhóm đợt: %{fullData.name}<br>"
            "Số đợt: %{y}<br>"
            "Thời lượng TB: %{customdata[0]:.1f} ngày<br>"
            "Đợt dài nhất: %{customdata[1]} ngày<br>"
            "Tổng số đợt: %{customdata[2]}<extra></extra>"
        )
    )
    fig.update_layout(
        title=f"Điểm nóng: đợt ô nhiễm ngắn hạn hay kéo dài? (AQI >= {threshold})",
        xaxis_title="Thành phố điểm nóng",
        yaxis_title="Số đợt ô nhiễm",
        height=430,
        barmode="stack",
        legend_title_text="Độ dài đợt",
    )
    fig.update_xaxes(tickangle=-30)
    return fig


def hotspot_persistence_bar(df: pd.DataFrame) -> go.Figure:
    """Bar + line combo for longest/average episode durations and long-episode share."""
    if df.empty:
        return line_placeholder("Độ kéo dài ô nhiễm tại các điểm nóng")

    sub = df.sort_values("longest_duration_days", ascending=False)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=sub["City"],
            y=sub["longest_duration_days"],
            name="Đợt dài nhất (ngày)",
            marker_color=CHART_COLOR_SEQUENCE[0],
            customdata=sub[["avg_duration_days", "total_episodes"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Đợt dài nhất: %{y} ngày<br>"
                "Thời lượng TB: %{customdata[0]:.1f} ngày<br>"
                "Tổng số đợt: %{customdata[1]}<extra></extra>"
            ),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=sub["City"],
            y=sub["long_episode_ratio"] * 100,
            mode="lines+markers",
            name="Tỷ lệ đợt dài >=8 ngày (%)",
            line=dict(color="#D62728", width=2),
            marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>Tỷ lệ đợt dài: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title="Mức độ kéo dài của ô nhiễm tại các điểm nóng",
        xaxis_title="Thành phố điểm nóng",
        height=430,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(title_text="Số ngày", secondary_y=False)
    fig.update_yaxes(title_text="Tỷ lệ (%)", secondary_y=True)
    return fig


def metro_pollutant_priority_bar(df: pd.DataFrame) -> go.Figure:
    """Rank pollutants by aggregated policy priority score across metros."""
    if df.empty:
        return line_placeholder("Ưu tiên chất ô nhiễm tại các đô thị lớn")

    sub = df.sort_values("priority_score", ascending=False)
    fig = px.bar(
        sub,
        x="pollutant",
        y="priority_score",
        color="mean_abs_corr",
        color_continuous_scale="YlOrRd",
        custom_data=["mean_abs_corr", "mean_severe_lift", "n_cities"],
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Điểm ưu tiên: %{y:.3f}<br>"
            "|Tương quan AQI| TB: %{customdata[0]:.3f}<br>"
            "Severe uplift TB: %{customdata[1]:.2f}x<br>"
            "Số đô thị: %{customdata[2]}<extra></extra>"
        )
    )
    fig.update_layout(
        title="Xếp hạng chất ô nhiễm cần ưu tiên kiểm soát (đô thị lớn)",
        xaxis_title="Chất ô nhiễm",
        yaxis_title="Điểm ưu tiên (0-1)",
        height=420,
        coloraxis_colorbar_title="|corr|",
    )
    return fig


def metro_pollutant_priority_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap of pollutant priority score across major metros."""
    if df.empty:
        return line_placeholder("Heatmap ưu tiên chất ô nhiễm theo đô thị")

    pivot = df.pivot_table(index="City", columns="pollutant", values="priority_score", aggfunc="mean")
    if pivot.empty:
        return line_placeholder("Heatmap ưu tiên chất ô nhiễm theo đô thị")

    city_order = df.groupby("City")["priority_score"].mean().sort_values(ascending=False).index.tolist()
    pollutant_order = (
        df.groupby("pollutant")["priority_score"]
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )
    pivot = pivot.reindex(index=city_order, columns=pollutant_order)

    fig = px.imshow(
        pivot,
        color_continuous_scale="YlOrRd",
        zmin=0,
        zmax=1,
        aspect="auto",
        labels={"x": "Chất ô nhiễm", "y": "Đô thị", "color": "Điểm ưu tiên"},
        text_auto=".2f",
    )
    fig.update_layout(
        title="Heatmap mức ưu tiên kiểm soát theo từng đô thị lớn",
        height=max(360, 36 * len(pivot.index) + 120),
    )
    fig.update_xaxes(tickangle=-30)
    return fig
