from __future__ import annotations

import unittest

from quantvibe.backtest.engine import BacktestEngine
from quantvibe.backtest.report import (
    build_backtest_export_frame,
    build_drawdown_frame,
    build_equity_frame,
    build_holdings_frame,
    build_latest_scores_frame,
    build_metrics_frame,
    build_normalized_price_frame,
    build_turnover_frame,
)
from quantvibe.factors.composite import FactorComposite
from quantvibe.factors.technical import MomentumFactor
from quantvibe.pipelines.research import ResearchPipeline
from tests.unit.test_research_pipeline import FakeProvider


class ReportBuildersTest(unittest.TestCase):
    def test_report_builders_return_non_empty_frames(self) -> None:
        pipeline = ResearchPipeline(
            provider=FakeProvider(),
            composite=FactorComposite([MomentumFactor()]),
            engine=BacktestEngine(periods_per_year=365, default_commission_bps=0.0, default_slippage_bps=0.0),
        )
        run = pipeline.run_full(symbols=["BTC/USDT", "ETH/USDT"], start="2024-01-01", top_n=1)
        self.assertFalse(build_equity_frame(run).empty)
        self.assertFalse(build_drawdown_frame(run).empty)
        self.assertFalse(build_metrics_frame(run).empty)
        self.assertFalse(build_backtest_export_frame(run).empty)
        self.assertFalse(build_normalized_price_frame(run).empty)
        self.assertFalse(build_latest_scores_frame(run).empty)
        self.assertFalse(build_holdings_frame(run).empty)
        self.assertFalse(build_turnover_frame(run).empty)
