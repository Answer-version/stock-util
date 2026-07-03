from __future__ import annotations

import pandas as pd

from quantvibe.data.validators import validate_universe_df


def build_static_universe(symbols: list[str], asset_type: str, exchange: str, snapshot_at: str) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "symbol": symbols,
            "asset_type": asset_type,
            "exchange": exchange,
            "listed_at": pd.NaT,
            "delisted_at": pd.NaT,
            "tradable": True,
            "industry": None,
            "universe_name": "static",
            "snapshot_at": pd.Timestamp(snapshot_at, tz="UTC"),
        }
    )
    return validate_universe_df(frame)
