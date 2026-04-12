"""Insights page data access and aggregations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from dashboard.config import POLLUTANT_COLUMNS
from dashboard.data.repositories import DatasetRepository
from dashboard.data.schema import COL_AQI, COL_CITY, COL_DATE


class InsightsData(DatasetRepository):
    """Insight-specific aggregates for hotspot persistence and pollutant priorities."""

    dataset_kind = "city_day"

    @staticmethod
    def kpi_summary(df: pd.DataFrame) -> dict[str, float | int]:
        if df.empty or COL_AQI not in df.columns:
            return {"mean_aqi": float("nan"), "median_aqi": float("nan"), "rows": len(df)}
        values = pd.to_numeric(df[COL_AQI], errors="coerce")
        return {
            "mean_aqi": float(values.mean()),
            "median_aqi": float(values.median()),
            "rows": int(len(df)),
        }

    @staticmethod
    def hotspot_episodes(
        df: pd.DataFrame,
        *,
        aqi_threshold: int = 200,
        top_n: int = 8,
    ) -> pd.DataFrame:
        required = {COL_CITY, COL_DATE, COL_AQI}
        if df.empty or not required.issubset(df.columns):
            return pd.DataFrame()

        t = df[[COL_CITY, COL_DATE, COL_AQI]].copy()
        t[COL_DATE] = pd.to_datetime(t[COL_DATE], errors="coerce")
        t[COL_AQI] = pd.to_numeric(t[COL_AQI], errors="coerce")
        t = t.dropna(subset=[COL_CITY, COL_DATE, COL_AQI])
        if t.empty:
            return pd.DataFrame()

        daily = (
            t.groupby([COL_CITY, COL_DATE], as_index=False)[COL_AQI]
            .mean()
            .sort_values([COL_CITY, COL_DATE])
        )
        daily["is_hot"] = daily[COL_AQI] >= aqi_threshold
        hot_counts = (
            daily[daily["is_hot"]]
            .groupby(COL_CITY, as_index=False)
            .size()
            .rename(columns={"size": "hot_days"})
            .sort_values("hot_days", ascending=False)
        )
        if hot_counts.empty:
            return pd.DataFrame()

        hot_cities = hot_counts.head(top_n)[COL_CITY].tolist()
        daily = daily[daily[COL_CITY].isin(hot_cities)]

        episodes: list[dict[str, object]] = []
        for city, group in daily.groupby(COL_CITY):
            hot = group[group["is_hot"]].sort_values(COL_DATE).copy()
            if hot.empty:
                continue
            hot["new_episode"] = hot[COL_DATE].diff().dt.days.ne(1)
            hot.loc[hot.index[0], "new_episode"] = True
            hot["episode_id"] = hot["new_episode"].cumsum()
            episode_df = (
                hot.groupby("episode_id", as_index=False)
                .agg(
                    start_date=(COL_DATE, "min"),
                    end_date=(COL_DATE, "max"),
                    duration_days=(COL_DATE, "size"),
                    mean_aqi=(COL_AQI, "mean"),
                    peak_aqi=(COL_AQI, "max"),
                )
                .drop(columns=["episode_id"])
            )
            episode_df[COL_CITY] = city
            episodes.extend(episode_df.to_dict("records"))

        if not episodes:
            return pd.DataFrame()
        return pd.DataFrame(episodes)

    @staticmethod
    def hotspot_duration_profile(
        df: pd.DataFrame,
        *,
        aqi_threshold: int = 200,
        top_n: int = 8,
    ) -> pd.DataFrame:
        episodes = InsightsData.hotspot_episodes(df, aqi_threshold=aqi_threshold, top_n=top_n)
        if episodes.empty:
            return pd.DataFrame()

        def duration_group(days: int) -> str:
            if days <= 3:
                return "Short (<=3d)"
            if days <= 7:
                return "Medium (4-7d)"
            return "Long (>=8d)"

        episodes["duration_group"] = episodes["duration_days"].astype(int).apply(duration_group)
        grouped = (
            episodes.groupby([COL_CITY, "duration_group"], as_index=False)
            .size()
            .rename(columns={"size": "episodes"})
        )
        totals = episodes.groupby(COL_CITY, as_index=False).agg(
            total_episodes=("duration_days", "count"),
            avg_duration_days=("duration_days", "mean"),
            longest_duration_days=("duration_days", "max"),
        )
        out = grouped.merge(totals, on=COL_CITY, how="left")
        order = ["Short (<=3d)", "Medium (4-7d)", "Long (>=8d)"]
        out["duration_group"] = pd.Categorical(out["duration_group"], categories=order, ordered=True)
        return out.sort_values([COL_CITY, "duration_group"]).reset_index(drop=True)

    @staticmethod
    def hotspot_persistence_by_city(
        df: pd.DataFrame,
        *,
        aqi_threshold: int = 200,
        top_n: int = 8,
    ) -> pd.DataFrame:
        episodes = InsightsData.hotspot_episodes(df, aqi_threshold=aqi_threshold, top_n=top_n)
        if episodes.empty:
            return pd.DataFrame()
        episodes["is_long"] = episodes["duration_days"] >= 8
        grouped = episodes.groupby(COL_CITY, as_index=False).agg(
            total_episodes=("duration_days", "count"),
            avg_duration_days=("duration_days", "mean"),
            longest_duration_days=("duration_days", "max"),
            long_episode_ratio=("is_long", "mean"),
        )
        return grouped.sort_values("longest_duration_days", ascending=False).reset_index(drop=True)

    @staticmethod
    def pollutant_priority_matrix(
        df: pd.DataFrame,
        *,
        aqi_threshold: int = 200,
        top_metros: int = 8,
    ) -> pd.DataFrame:
        required = {COL_CITY, COL_AQI, *POLLUTANT_COLUMNS}
        if df.empty or not required.issubset(df.columns):
            return pd.DataFrame()

        t = df[[COL_CITY, COL_AQI, *POLLUTANT_COLUMNS]].copy()
        t[COL_AQI] = pd.to_numeric(t[COL_AQI], errors="coerce")
        for pollutant in POLLUTANT_COLUMNS:
            t[pollutant] = pd.to_numeric(t[pollutant], errors="coerce")
        t = t.dropna(subset=[COL_CITY, COL_AQI])
        if t.empty:
            return pd.DataFrame()

        metros = (
            t.groupby(COL_CITY, as_index=False)
            .size()
            .rename(columns={"size": "n_rows"})
            .sort_values("n_rows", ascending=False)
            .head(top_metros)[COL_CITY]
            .tolist()
        )
        if not metros:
            return pd.DataFrame()

        records: list[dict[str, object]] = []
        for city in metros:
            city_df = t[t[COL_CITY] == city].copy()
            severe = city_df[city_df[COL_AQI] >= aqi_threshold]
            city_scores: list[dict[str, float | str]] = []

            for pollutant in POLLUTANT_COLUMNS:
                pair = city_df[[COL_AQI, pollutant]].dropna()
                if len(pair) < 30:
                    continue
                corr = float(pair[pollutant].corr(pair[COL_AQI]))
                overall_mean = float(pair[pollutant].mean())
                severe_pair = severe[[pollutant]].dropna()
                severe_mean = float(severe_pair[pollutant].mean()) if not severe_pair.empty else float("nan")
                severe_lift = severe_mean / overall_mean if overall_mean > 0 else float("nan")
                city_scores.append(
                    {
                        COL_CITY: city,
                        "pollutant": pollutant,
                        "corr": corr,
                        "abs_corr": abs(corr),
                        "severe_lift": severe_lift,
                        "n_obs": int(len(pair)),
                    }
                )

            if not city_scores:
                continue

            city_scores_df = pd.DataFrame(city_scores)
            max_abs_corr = city_scores_df["abs_corr"].max()
            max_lift = city_scores_df["severe_lift"].replace([np.inf, -np.inf], np.nan).max()
            city_scores_df["corr_norm"] = (
                city_scores_df["abs_corr"] / max_abs_corr
                if pd.notna(max_abs_corr) and max_abs_corr > 0
                else 0.0
            )
            city_scores_df["lift_norm"] = (
                city_scores_df["severe_lift"] / max_lift
                if pd.notna(max_lift) and max_lift > 0
                else 0.0
            )
            city_scores_df["priority_score"] = (
                0.65 * city_scores_df["corr_norm"] + 0.35 * city_scores_df["lift_norm"]
            )
            records.extend(city_scores_df.to_dict("records"))

        if not records:
            return pd.DataFrame()
        out = pd.DataFrame(records)
        out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["priority_score"])
        return out.sort_values([COL_CITY, "priority_score"], ascending=[True, False]).reset_index(drop=True)

    @staticmethod
    def pollutant_priority_summary(priority_matrix: pd.DataFrame) -> pd.DataFrame:
        if priority_matrix.empty:
            return pd.DataFrame()
        grouped = priority_matrix.groupby("pollutant", as_index=False).agg(
            priority_score=("priority_score", "mean"),
            mean_abs_corr=("abs_corr", "mean"),
            mean_severe_lift=("severe_lift", "mean"),
            n_cities=(COL_CITY, "nunique"),
        )
        return grouped.sort_values("priority_score", ascending=False).reset_index(drop=True)
