from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

FreqType = Literal["1m", "5m", "15m", "30m", "1h", "1d"]
AssetType = Literal["crypto", "a_share", "us_stock"]
PriceAdjustType = Literal["raw", "split", "qfq", "hfq"]
ExecutionPriceType = Literal["next_open", "next_close"]


@dataclass(slots=True)
class BacktestResult:
    returns: pd.Series
    equity_curve: pd.Series
    metrics: dict[str, float]
    weights: pd.DataFrame
    turnover: pd.Series
