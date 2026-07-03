from __future__ import annotations

import numpy as np
import pandas as pd


def winsorize_by_date(series: pd.Series, lower: float = 0.05, upper: float = 0.95) -> pd.Series:
    def _clip(group: pd.Series) -> pd.Series:
        lo = group.quantile(lower)
        hi = group.quantile(upper)
        return group.clip(lower=lo, upper=hi)

    return series.groupby(level="datetime", group_keys=False).apply(_clip)


def zscore_by_date(series: pd.Series) -> pd.Series:
    def _zscore(group: pd.Series) -> pd.Series:
        std = group.std(ddof=0)
        if pd.isna(std) or std == 0:
            return pd.Series(0.0, index=group.index)
        return (group - group.mean()) / std

    return series.groupby(level="datetime", group_keys=False).apply(_zscore)


def rank_pct_by_date(series: pd.Series, ascending: bool = True) -> pd.Series:
    return series.groupby(level="datetime", group_keys=False).rank(pct=True, ascending=ascending)


def fill_missing_by_date(series: pd.Series, value: float = 0.0) -> pd.Series:
    return series.groupby(level="datetime", group_keys=False).apply(lambda group: group.fillna(value))


def combine_weighted(factor_values: dict[str, pd.Series], weights: dict[str, float]) -> pd.Series:
    combined: pd.Series | None = None
    for name, series in factor_values.items():
        weighted = series * weights[name]
        combined = weighted if combined is None else combined.add(weighted, fill_value=0.0)
    if combined is None:
        raise ValueError("no factor values to combine")
    return combined.rename("composite_score")
