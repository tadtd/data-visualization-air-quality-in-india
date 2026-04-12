"""Shared dataset access classes for dashboard pages."""

from __future__ import annotations

from typing import ClassVar

import pandas as pd

from dashboard.data.loader import load_dataset
from dashboard.data.schema import DatasetKind, FilterState
from dashboard.data.transforms import apply_filters


class DatasetRepository:
    """Dataset-agnostic base for page data classes."""

    dataset_kind: ClassVar[DatasetKind | None] = None

    @classmethod
    def load_frame(cls, kind: DatasetKind | None = None) -> pd.DataFrame:
        """Load a dataset frame or return an empty frame when the file is missing."""
        resolved_kind = kind or cls.dataset_kind
        if resolved_kind is None:
            raise ValueError("A dataset kind must be provided.")

        df = load_dataset(resolved_kind)
        return df if df is not None else pd.DataFrame()

    @staticmethod
    def apply_filter_state(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
        """Subset a frame using the shared filter model."""
        return apply_filters(df, filters)


def load_dataset_frame(kind: DatasetKind) -> pd.DataFrame:
    """Functional alias for :meth:`DatasetRepository.load_frame`."""
    return DatasetRepository.load_frame(kind)
