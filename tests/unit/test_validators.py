from __future__ import annotations

import pandas as pd
import unittest

from quantvibe.core.exceptions import SchemaValidationError
from quantvibe.data.validators import validate_bars_df


def make_bars_df() -> pd.DataFrame:
    datetimes = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    index = pd.MultiIndex.from_product([datetimes, ["BTC/USDT", "ETH/USDT"]], names=["datetime", "symbol"])
    return pd.DataFrame(
        {
            "open": [1, 2, 3, 4, 5, 6],
            "high": [1, 2, 3, 4, 5, 6],
            "low": [1, 2, 3, 4, 5, 6],
            "close": [1, 2, 3, 4, 5, 6],
            "volume": [10, 11, 12, 13, 14, 15],
        },
        index=index,
    ).sort_index()


class ValidatorsTest(unittest.TestCase):
    def test_validate_bars_df_accepts_normalized_panel(self) -> None:
        df = make_bars_df()
        validated = validate_bars_df(df)
        pd.testing.assert_frame_equal(validated, df)

    def test_validate_bars_df_rejects_naive_timestamps(self) -> None:
        df = make_bars_df().reset_index()
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(None)
        df = df.set_index(["datetime", "symbol"])
        with self.assertRaises(SchemaValidationError):
            validate_bars_df(df)
