from __future__ import annotations

import pandas as pd
import unittest
from unittest.mock import patch

from quantvibe.data.providers.crypto_ccxt import CryptoCCXTProvider


class FakeExchange:
    id = "fake"

    def __init__(self) -> None:
        self.calls = 0

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: int, limit: int = 1000):
        self.calls += 1
        if self.calls == 1:
            return [
                [1704067200000, 100, 101, 99, 100.5, 10],
                [1704153600000, 110, 111, 109, 110.5, 11],
            ]
        return []


class FailingExchange:
    def fetch_ohlcv(self, symbol: str, timeframe: str, since: int, limit: int = 1000):
        raise RuntimeError("upstream timeout")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class CryptoProviderTest(unittest.TestCase):
    def test_crypto_provider_normalizes_multi_symbol_bars(self) -> None:
        exchange = FakeExchange()
        provider = CryptoCCXTProvider(exchange=exchange, cache=None)
        bars = provider.get_bars(symbols=["BTC/USDT"], freq="1d", start="2024-01-01", end="2024-01-02")
        self.assertIsInstance(bars, pd.DataFrame)
        self.assertEqual(bars.index.names, ["datetime", "symbol"])
        self.assertEqual(list(bars.columns), ["open", "high", "low", "close", "volume"])
        self.assertIsNotNone(bars.index.get_level_values("datetime").tz)
        self.assertIn(
            (pd.Timestamp("2024-01-01 00:00:00+00:00"), "BTC/USDT"),
            list(bars.index),
        )

    @patch("quantvibe.data.providers.crypto_ccxt.requests.get")
    def test_crypto_provider_falls_back_to_okx_rest(self, mock_get) -> None:
        mock_get.side_effect = [
            FakeResponse(
                {
                    "data": [
                        ["1704153600000", "110", "111", "109", "110.5", "11"],
                        ["1704067200000", "100", "101", "99", "100.5", "10"],
                    ]
                }
            )
        ]
        provider = CryptoCCXTProvider(exchange=FailingExchange(), cache=None)
        bars = provider.get_bars(symbols=["BTC/USDT"], freq="1d", start="2024-01-01", end="2024-01-02")
        self.assertEqual(len(bars), 2)
        self.assertEqual(float(bars.iloc[0]["close"]), 100.5)
