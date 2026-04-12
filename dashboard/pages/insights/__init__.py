"""Insights page package."""

from dashboard.pages.insights.charts import InsightsCharts
from dashboard.pages.insights.data import InsightsData
from dashboard.pages.insights.view import render

__all__ = ["InsightsCharts", "InsightsData", "render"]
