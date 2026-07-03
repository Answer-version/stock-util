from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Factor(ABC):
    name: str = ""
    category: str = ""
    required_columns: tuple[str, ...] = ()

    def validate_inputs(self, panel_df: pd.DataFrame) -> None:
        missing = [column for column in self.required_columns if column not in panel_df.columns]
        if missing:
            raise ValueError(f"{self.name} missing required columns: {missing}")
        if not isinstance(panel_df.index, pd.MultiIndex):
            raise ValueError(f"{self.name} expects MultiIndex input")

    @abstractmethod
    def compute(self, panel_df: pd.DataFrame, **kwargs) -> pd.Series:
        """Compute a factor on a [datetime, symbol] panel."""
