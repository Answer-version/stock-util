from __future__ import annotations

import pandas as pd

from quantvibe.factors.base import Factor
from quantvibe.factors.preprocess import combine_weighted, fill_missing_by_date, winsorize_by_date, zscore_by_date


class FactorComposite:
    def __init__(self, factors: list[Factor], weights: dict[str, float] | None = None) -> None:
        if not factors:
            raise ValueError("at least one factor is required")
        self.factors = factors
        equal_weight = 1.0 / len(factors)
        self.weights = weights or {factor.name: equal_weight for factor in factors}

    def score(self, panel_df: pd.DataFrame) -> pd.Series:
        normalized: dict[str, pd.Series] = {}
        for factor in self.factors:
            raw = factor.compute(panel_df)
            clipped = winsorize_by_date(raw)
            standardized = zscore_by_date(clipped)
            normalized[factor.name] = fill_missing_by_date(standardized, value=0.0)
        return combine_weighted(normalized, self.weights)
