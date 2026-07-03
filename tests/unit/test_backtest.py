from __future__ import annotations

import pandas as pd
import unittest

from quantvibe.backtest.engine import BacktestEngine


def make_prices() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
    symbols = ["BTC/USDT", "ETH/USDT"]
    index = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "symbol"])
    rows = [
        {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
        {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
        {"open": 110, "high": 111, "low": 109, "close": 110, "volume": 10},
        {"open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
        {"open": 121, "high": 122, "low": 120, "close": 121, "volume": 10},
        {"open": 81, "high": 82, "low": 80, "close": 81, "volume": 10},
        {"open": 133.1, "high": 134, "low": 132, "close": 133.1, "volume": 10},
        {"open": 72.9, "high": 73, "low": 72, "close": 72.9, "volume": 10},
        {"open": 146.41, "high": 147, "low": 145, "close": 146.41, "volume": 10},
        {"open": 65.61, "high": 66, "low": 65, "close": 65.61, "volume": 10},
    ]
    return pd.DataFrame(rows, index=index)


def make_scores() -> pd.Series:
    dates = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
    index = pd.MultiIndex.from_product([dates, ["BTC/USDT", "ETH/USDT"]], names=["datetime", "symbol"])
    scores = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    return pd.Series(scores, index=index, name="score")


class BacktestEngineTest(unittest.TestCase):
    def test_backtest_engine_respects_next_open_lag(self) -> None:
        engine = BacktestEngine(periods_per_year=365, default_commission_bps=0.0, default_slippage_bps=0.0)
        result = engine.run(make_prices(), make_scores(), top_n=1)
        self.assertEqual(result.returns.index[0], pd.Timestamp("2024-01-01", tz="UTC"))
        self.assertEqual(result.returns.iloc[0], 0.0)
        self.assertAlmostEqual(result.returns.iloc[1], 0.1)
        self.assertGreater(result.metrics["total_return"], 0.0)
        self.assertFalse(result.weights.empty)
