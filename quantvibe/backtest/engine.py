from __future__ import annotations

import pandas as pd

from quantvibe.backtest.metrics import compute_metrics
from quantvibe.core.types import BacktestResult, ExecutionPriceType
from quantvibe.data.validators import validate_bars_df
from quantvibe.portfolio.construction import top_n_equal_weight


class BacktestEngine:
    def __init__(
        self,
        periods_per_year: int = 365,
        default_commission_bps: float = 10.0,
        default_slippage_bps: float = 5.0,
    ) -> None:
        self.periods_per_year = periods_per_year
        self.default_commission_bps = default_commission_bps
        self.default_slippage_bps = default_slippage_bps

    def run(
        self,
        prices: pd.DataFrame,
        scores: pd.Series,
        rebalance_freq: str = "1D",
        top_n: int = 10,
        execution_price: ExecutionPriceType = "next_open",
        commission_bps: float | None = None,
        slippage_bps: float | None = None,
    ) -> BacktestResult:
        if execution_price != "next_open":
            raise NotImplementedError("Phase 1 only supports next_open execution")
        validate_bars_df(prices)
        if not isinstance(scores.index, pd.MultiIndex):
            raise ValueError("scores must use [datetime, symbol] MultiIndex")

        open_wide = prices["open"].unstack("symbol").sort_index()
        score_wide = scores.unstack("symbol").reindex(open_wide.index).sort_index()

        if rebalance_freq != "1D":
            score_wide = score_wide.resample(rebalance_freq).last().reindex(open_wide.index).ffill()

        target_weights = top_n_equal_weight(score_wide, top_n=top_n)
        live_weights = target_weights.shift(1).fillna(0.0)
        asset_returns = (open_wide.shift(-1) / open_wide) - 1.0
        gross_returns = (live_weights * asset_returns).sum(axis=1, min_count=1).fillna(0.0)

        turnover = live_weights.diff().abs().sum(axis=1)
        if not turnover.empty:
            turnover.iloc[0] = live_weights.iloc[0].abs().sum()

        total_cost_bps = (commission_bps if commission_bps is not None else self.default_commission_bps) + (
            slippage_bps if slippage_bps is not None else self.default_slippage_bps
        )
        net_returns = gross_returns - turnover * (total_cost_bps / 10_000.0)
        if not net_returns.empty:
            net_returns = net_returns.iloc[:-1]
            turnover = turnover.reindex(net_returns.index).fillna(0.0)
            live_weights = live_weights.reindex(net_returns.index).fillna(0.0)

        equity_curve = (1.0 + net_returns).cumprod()
        metrics = compute_metrics(net_returns, turnover, periods_per_year=self.periods_per_year)
        weights_long = (
            live_weights.stack()
            .rename("weight")
            .reset_index()
            .query("weight != 0")
            .set_index(["datetime", "symbol"])
            .sort_index()
        )
        return BacktestResult(
            returns=net_returns.rename("portfolio_return"),
            equity_curve=equity_curve.rename("equity_curve"),
            metrics=metrics,
            weights=weights_long,
            turnover=turnover.rename("turnover"),
        )
