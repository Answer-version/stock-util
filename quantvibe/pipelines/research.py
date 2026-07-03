from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quantvibe.backtest.engine import BacktestEngine
from quantvibe.core.types import BacktestResult
from quantvibe.data.base import BaseProvider
from quantvibe.factors.composite import FactorComposite


@dataclass(slots=True)
class ResearchRun:
    prices: pd.DataFrame
    scores: pd.Series
    backtest: BacktestResult


class ResearchPipeline:
    def __init__(
        self,
        provider: BaseProvider,
        composite: FactorComposite,
        engine: BacktestEngine,
    ) -> None:
        self.provider = provider
        self.composite = composite
        self.engine = engine

    def run_full(
        self,
        symbols: list[str],
        start: str,
        end: str | None = None,
        freq: str = "1d",
        top_n: int = 2,
    ) -> ResearchRun:
        prices = self.provider.get_bars(symbols=symbols, freq=freq, start=start, end=end)
        scores = self.composite.score(prices)
        backtest = self.engine.run(prices=prices, scores=scores, top_n=top_n)
        return ResearchRun(prices=prices, scores=scores, backtest=backtest)

    def run(
        self,
        symbols: list[str],
        start: str,
        end: str | None = None,
        freq: str = "1d",
        top_n: int = 2,
    ) -> BacktestResult:
        return self.run_full(symbols=symbols, start=start, end=end, freq=freq, top_n=top_n).backtest
