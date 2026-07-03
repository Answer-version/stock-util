from __future__ import annotations

import numpy as np
import pandas as pd
import unittest

from quantvibe.factors.composite import FactorComposite
from quantvibe.factors.technical import MAGapFactor, MomentumFactor, RSI14Factor, VolatilityFactor, VolumeRatioFactor


def make_panel() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=40, freq="D", tz="UTC")
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    index = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "symbol"])
    rows = []
    for date_idx, _date in enumerate(dates):
        for symbol_idx, _symbol in enumerate(symbols):
            base = 100 + (date_idx * (symbol_idx + 1))
            rows.append(
                {
                    "open": base,
                    "high": base + 1,
                    "low": base - 1,
                    "close": base + 0.5,
                    "volume": 1_000 + (symbol_idx * 100) + (date_idx * 10),
                }
            )
    return pd.DataFrame(rows, index=index)


class FactorsTest(unittest.TestCase):
    def test_technical_factors_return_multiindex_series(self) -> None:
        panel = make_panel()
        factors = [MomentumFactor(), VolatilityFactor(), RSI14Factor(), MAGapFactor(), VolumeRatioFactor()]
        for factor in factors:
            result = factor.compute(panel)
            self.assertIsInstance(result, pd.Series)
            self.assertEqual(result.index.names, ["datetime", "symbol"])
            self.assertEqual(result.name, factor.name)
            self.assertGreater(result.notna().sum(), 0)

    def test_factor_composite_produces_cross_sectional_scores(self) -> None:
        panel = make_panel()
        composite = FactorComposite(
            factors=[MomentumFactor(), VolatilityFactor(), RSI14Factor(), MAGapFactor(), VolumeRatioFactor()]
        )
        score = composite.score(panel)
        self.assertIsInstance(score, pd.Series)
        self.assertEqual(score.index.names, ["datetime", "symbol"])
        sample_day = score.xs(pd.Timestamp("2024-02-09", tz="UTC"), level="datetime")
        self.assertTrue(np.isfinite(sample_day).all())
