from __future__ import annotations

import numpy as np
import pandas as pd


def compute_max_drawdown(equity_curve: pd.Series) -> float:
    rolling_peak = equity_curve.cummax()
    drawdown = (equity_curve / rolling_peak) - 1.0
    return float(drawdown.min()) if not drawdown.empty else 0.0


def compute_metrics(
    returns: pd.Series,
    turnover: pd.Series,
    periods_per_year: int,
) -> dict[str, float]:
    clean_returns = returns.dropna()
    if clean_returns.empty:
        return {
            "total_return": 0.0,
            "annual_return": 0.0,
            "annual_volatility": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "calmar": 0.0,
            "win_rate": 0.0,
            "avg_turnover": float(turnover.mean()) if not turnover.empty else 0.0,
        }

    equity_curve = (1.0 + clean_returns).cumprod()
    total_return = equity_curve.iloc[-1] - 1.0
    annual_return = (1.0 + total_return) ** (periods_per_year / len(clean_returns)) - 1.0
    annual_volatility = clean_returns.std(ddof=0) * np.sqrt(periods_per_year)
    sharpe = annual_return / annual_volatility if annual_volatility else 0.0
    max_drawdown = abs(compute_max_drawdown(equity_curve))
    calmar = annual_return / max_drawdown if max_drawdown else 0.0
    win_rate = float((clean_returns > 0).mean())
    return {
        "total_return": float(total_return),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_volatility),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_drawdown),
        "calmar": float(calmar),
        "win_rate": win_rate,
        "avg_turnover": float(turnover.reindex(clean_returns.index).fillna(0.0).mean()),
    }
