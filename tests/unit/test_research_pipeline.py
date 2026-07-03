from __future__ import annotations

import pandas as pd
import unittest

from quantvibe.backtest.engine import BacktestEngine
from quantvibe.data.base import BaseProvider
from quantvibe.factors.composite import FactorComposite
from quantvibe.factors.technical import MomentumFactor
from quantvibe.pipelines.research import ResearchPipeline


class FakeProvider(BaseProvider):
    asset_type = "crypto"
    provider_name = "fake"

    def get_bars(
        self,
        symbols: list[str],
        freq: str,
        start: str,
        end: str | None = None,
        adjust: str = "raw",
    ) -> pd.DataFrame:
        dates = pd.date_range("2024-01-01", periods=30, freq="D", tz="UTC")
        index = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "symbol"])
        rows = []
        for date_idx, _date in enumerate(dates):
            for symbol_idx, _symbol in enumerate(symbols):
                price = 100 + (date_idx * (symbol_idx + 1))
                rows.append(
                    {
                        "open": price,
                        "high": price + 1,
                        "low": price - 1,
                        "close": price + 0.5,
                        "volume": 1_000 + date_idx + symbol_idx,
                    }
                )
        return pd.DataFrame(rows, index=index)

    def get_universe(self, as_of: str, universe_name: str | None = None) -> pd.DataFrame:
        raise NotImplementedError


class ResearchPipelineTest(unittest.TestCase):
    def test_run_full_returns_prices_scores_and_backtest(self) -> None:
        pipeline = ResearchPipeline(
            provider=FakeProvider(),
            composite=FactorComposite([MomentumFactor()]),
            engine=BacktestEngine(periods_per_year=365, default_commission_bps=0.0, default_slippage_bps=0.0),
        )
        run = pipeline.run_full(symbols=["BTC/USDT", "ETH/USDT"], start="2024-01-01", top_n=1)
        self.assertFalse(run.prices.empty)
        self.assertFalse(run.scores.empty)
        self.assertIn("total_return", run.backtest.metrics)
