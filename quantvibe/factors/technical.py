from __future__ import annotations

import numpy as np
import pandas as pd

from quantvibe.factors.base import Factor


def _grouped_column(panel_df: pd.DataFrame, column: str) -> pd.core.groupby.generic.SeriesGroupBy:
    return panel_df[column].groupby(level="symbol", group_keys=False)


class MomentumFactor(Factor):
    name = "momentum_20"
    category = "technical"
    required_columns = ("close",)

    def compute(self, panel_df: pd.DataFrame, window: int = 20, **kwargs) -> pd.Series:
        self.validate_inputs(panel_df)
        series = _grouped_column(panel_df, "close").pct_change(window)
        return series.rename(self.name)


class VolatilityFactor(Factor):
    name = "volatility_20"
    category = "technical"
    required_columns = ("close",)

    def compute(self, panel_df: pd.DataFrame, window: int = 20, **kwargs) -> pd.Series:
        self.validate_inputs(panel_df)
        close = _grouped_column(panel_df, "close")
        series = close.pct_change().groupby(level="symbol", group_keys=False).rolling(window).std()
        series = series.droplevel(0)
        return (-series).rename(self.name)


class RSI14Factor(Factor):
    name = "rsi_14"
    category = "technical"
    required_columns = ("close",)

    def compute(self, panel_df: pd.DataFrame, window: int = 14, **kwargs) -> pd.Series:
        self.validate_inputs(panel_df)
        close = panel_df["close"]
        delta = close.groupby(level="symbol", group_keys=False).diff()
        gains = delta.clip(lower=0.0)
        losses = -delta.clip(upper=0.0)
        avg_gain = gains.groupby(level="symbol", group_keys=False).rolling(window).mean().droplevel(0)
        avg_loss = losses.groupby(level="symbol", group_keys=False).rolling(window).mean().droplevel(0)
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi = rsi.where(~((avg_loss == 0.0) & (avg_gain > 0.0)), 100.0)
        rsi = rsi.where(~((avg_loss == 0.0) & (avg_gain == 0.0)), 50.0)
        return rsi.rename(self.name)


class MAGapFactor(Factor):
    name = "ma_gap_5_20"
    category = "technical"
    required_columns = ("close",)

    def compute(self, panel_df: pd.DataFrame, short_window: int = 5, long_window: int = 20, **kwargs) -> pd.Series:
        self.validate_inputs(panel_df)
        close = _grouped_column(panel_df, "close")
        short_ma = close.rolling(short_window).mean().droplevel(0)
        long_ma = close.rolling(long_window).mean().droplevel(0)
        series = (short_ma / long_ma) - 1.0
        return series.rename(self.name)


class VolumeRatioFactor(Factor):
    name = "volume_ratio_20"
    category = "technical"
    required_columns = ("volume",)

    def compute(self, panel_df: pd.DataFrame, window: int = 20, **kwargs) -> pd.Series:
        self.validate_inputs(panel_df)
        volume = _grouped_column(panel_df, "volume")
        mean_volume = volume.rolling(window).mean().droplevel(0)
        series = panel_df["volume"] / mean_volume
        return series.rename(self.name)
