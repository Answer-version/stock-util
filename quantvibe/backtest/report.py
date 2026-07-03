from __future__ import annotations

import pandas as pd

from quantvibe.pipelines.research import ResearchRun


def build_equity_frame(run: ResearchRun) -> pd.DataFrame:
    frame = pd.concat([run.backtest.equity_curve, run.backtest.returns], axis=1)
    return frame.reset_index()


def build_drawdown_frame(run: ResearchRun) -> pd.DataFrame:
    equity = run.backtest.equity_curve
    peak = equity.cummax()
    drawdown = (equity / peak) - 1.0
    frame = pd.DataFrame({"drawdown": drawdown})
    return frame.reset_index()


def build_normalized_price_frame(run: ResearchRun) -> pd.DataFrame:
    close_wide = run.prices["close"].unstack("symbol").sort_index()
    normalized = close_wide.divide(close_wide.iloc[0]).mul(100.0)
    normalized.index.name = "datetime"
    return normalized.reset_index().melt(id_vars="datetime", var_name="symbol", value_name="normalized_price")


def build_latest_scores_frame(run: ResearchRun, lookback: int = 20) -> pd.DataFrame:
    score_wide = run.scores.unstack("symbol").sort_index().tail(lookback)
    score_wide.index.name = "datetime"
    return score_wide.reset_index().melt(id_vars="datetime", var_name="symbol", value_name="score")


def build_holdings_frame(run: ResearchRun) -> pd.DataFrame:
    weights = run.backtest.weights.reset_index()
    if weights.empty:
        return pd.DataFrame(columns=["datetime", "symbol", "weight"])
    return weights


def build_turnover_frame(run: ResearchRun) -> pd.DataFrame:
    return run.backtest.turnover.reset_index()


def build_metrics_frame(run: ResearchRun) -> pd.DataFrame:
    return pd.DataFrame(
        [{"metric": key, "value": value} for key, value in run.backtest.metrics.items()]
    )


def build_backtest_export_frame(run: ResearchRun) -> pd.DataFrame:
    equity = build_equity_frame(run)
    turnover = build_turnover_frame(run)
    merged = equity.merge(turnover, on="datetime", how="left")
    merged["turnover"] = merged["turnover"].fillna(0.0)
    return merged
