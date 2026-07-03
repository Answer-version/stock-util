from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
import time

from quantvibe.core.calendar import ensure_utc
from quantvibe.core.exceptions import DataSourceUnavailable, UnsupportedFreqError
from quantvibe.core.types import AssetType, FreqType, PriceAdjustType
from quantvibe.data.base import BaseProvider
from quantvibe.data.cache import DataCache
from quantvibe.data.validators import validate_bars_df, validate_universe_df


@dataclass(slots=True)
class _FetchWindow:
    start_ms: int
    end_ms: int | None


class CryptoCCXTProvider(BaseProvider):
    asset_type: AssetType = "crypto"
    provider_name = "crypto_ccxt"
    _timeframe_ms = {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "30m": 1_800_000,
        "1h": 3_600_000,
        "1d": 86_400_000,
    }

    def __init__(
        self,
        exchange_id: str = "binance",
        cache: DataCache | None = None,
        exchange: Any | None = None,
        cache_ttl_seconds: int = 86400,
        request_timeout_ms: int = 30_000,
    ) -> None:
        self.exchange_id = exchange_id
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds
        self.request_timeout_ms = request_timeout_ms
        self._exchange = exchange

    @property
    def exchange(self) -> Any:
        if self._exchange is None:
            try:
                import ccxt
            except ImportError as exc:
                raise DataSourceUnavailable("ccxt is required for CryptoCCXTProvider") from exc
            exchange_cls = getattr(ccxt, self.exchange_id)
            self._exchange = exchange_cls(
                {
                    "enableRateLimit": True,
                    "timeout": self.request_timeout_ms,
                }
            )
        return self._exchange

    def get_bars(
        self,
        symbols: list[str],
        freq: FreqType,
        start: str,
        end: str | None = None,
        adjust: PriceAdjustType = "raw",
    ) -> pd.DataFrame:
        if adjust != "raw":
            raise UnsupportedFreqError("crypto provider only supports raw prices")
        if freq not in self._timeframe_ms:
            raise UnsupportedFreqError(f"unsupported frequency: {freq}")

        frames: list[pd.DataFrame] = []
        for symbol in symbols:
            cache_key = {
                "provider": self.provider_name,
                "exchange_id": self.exchange_id,
                "symbol": symbol,
                "freq": freq,
                "start": start,
                "end": end,
                "adjust": adjust,
                "schema_version": "v1",
            }
            cached = self.cache.get(cache_key) if self.cache else None
            if cached is not None:
                frames.append(validate_bars_df(cached))
                continue
            rows = self._fetch_symbol_ohlcv(symbol, freq, start, end)
            frame = self._normalize_ohlcv(symbol, rows)
            if self.cache:
                self.cache.set(cache_key, frame, ttl_seconds=self.cache_ttl_seconds)
            frames.append(frame)

        combined = pd.concat(frames).sort_index()
        return validate_bars_df(combined)

    def get_universe(
        self,
        as_of: str,
        universe_name: str | None = None,
    ) -> pd.DataFrame:
        try:
            markets = self.exchange.load_markets()
        except Exception as exc:
            raise DataSourceUnavailable(f"failed to load markets from {self.exchange_id}") from exc

        symbols = []
        for market in markets.values():
            if not market.get("active", True):
                continue
            if market.get("spot") is not True:
                continue
            if market.get("quote") != "USDT":
                continue
            symbols.append(market["symbol"])
        frame = pd.DataFrame(
            {
                "symbol": sorted(symbols),
                "asset_type": self.asset_type,
                "exchange": self.exchange_id,
                "listed_at": pd.NaT,
                "delisted_at": pd.NaT,
                "tradable": True,
                "industry": None,
                "universe_name": universe_name or "spot_usdt",
                "snapshot_at": ensure_utc(as_of),
            }
        )
        return validate_universe_df(frame)

    def _fetch_symbol_ohlcv(
        self,
        symbol: str,
        freq: FreqType,
        start: str,
        end: str | None,
    ) -> list[list[float]]:
        try:
            return self._fetch_symbol_ohlcv_ccxt(symbol, freq, start, end)
        except DataSourceUnavailable as primary_exc:
            if freq == "1d":
                try:
                    return self._fetch_symbol_ohlcv_okx(symbol, start, end)
                except DataSourceUnavailable as fallback_exc:
                    raise DataSourceUnavailable(
                        f"failed to fetch ohlcv for {symbol}; primary source {self.exchange_id} and OKX fallback both failed"
                    ) from fallback_exc
            raise primary_exc

    def _fetch_symbol_ohlcv_ccxt(
        self,
        symbol: str,
        freq: FreqType,
        start: str,
        end: str | None,
    ) -> list[list[float]]:
        window = _FetchWindow(
            start_ms=int(ensure_utc(start).timestamp() * 1000),
            end_ms=int(ensure_utc(end).timestamp() * 1000) if end else None,
        )
        timeframe_ms = self._timeframe_ms[freq]
        cursor = window.start_ms
        rows: list[list[float]] = []

        while True:
            try:
                batch = self.exchange.fetch_ohlcv(symbol, timeframe=freq, since=cursor, limit=1000)
            except Exception as exc:
                raise DataSourceUnavailable(f"failed to fetch ohlcv for {symbol}") from exc
            if not batch:
                break
            rows.extend(batch)
            last_ts = int(batch[-1][0])
            next_cursor = last_ts + timeframe_ms
            if next_cursor <= cursor:
                break
            cursor = next_cursor
            if window.end_ms is not None and cursor > window.end_ms:
                break
            if len(batch) < 1000:
                break

        if window.end_ms is not None:
            rows = [row for row in rows if int(row[0]) <= window.end_ms]
        deduped: dict[int, list[float]] = {}
        for row in rows:
            deduped[int(row[0])] = row
        return [deduped[key] for key in sorted(deduped)]

    def _fetch_symbol_ohlcv_okx(
        self,
        symbol: str,
        start: str,
        end: str | None,
    ) -> list[list[float]]:
        if "/" not in symbol:
            raise DataSourceUnavailable(f"unsupported crypto symbol format for OKX fallback: {symbol}")

        start_ms = int(ensure_utc(start).timestamp() * 1000)
        end_ms = int(ensure_utc(end).timestamp() * 1000) if end else None
        inst_id = symbol.replace("/", "-")
        url = "https://www.okx.com/api/v5/market/history-candles"
        after: str | None = str(end_ms + 1) if end_ms is not None else None
        rows: list[list[float]] = []

        while True:
            params = {
                "instId": inst_id,
                "bar": "1D",
                "limit": "100",
            }
            if after is not None:
                params["after"] = after
            payload = None
            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    response = requests.get(url, params=params, timeout=self.request_timeout_ms / 1000)
                    response.raise_for_status()
                    payload = response.json()
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(1.0 + attempt)
            if payload is None:
                raise DataSourceUnavailable(f"OKX fallback request failed for {symbol}") from last_error

            batch = payload.get("data") or []
            if not batch:
                break

            for item in batch:
                timestamp_ms = int(item[0])
                if timestamp_ms < start_ms:
                    continue
                if end_ms is not None and timestamp_ms > end_ms:
                    continue
                rows.append(
                    [
                        timestamp_ms,
                        float(item[1]),
                        float(item[2]),
                        float(item[3]),
                        float(item[4]),
                        float(item[5]),
                    ]
                )

            oldest_ts = int(batch[-1][0])
            if oldest_ts <= start_ms or len(batch) < 100:
                break
            after = str(oldest_ts)

        deduped: dict[int, list[float]] = {}
        for row in rows:
            deduped[int(row[0])] = row
        return [deduped[key] for key in sorted(deduped)]

    def _normalize_ohlcv(self, symbol: str, rows: list[list[float]]) -> pd.DataFrame:
        if not rows:
            empty_index = pd.MultiIndex.from_arrays(
                [
                    pd.DatetimeIndex([], tz="UTC", name="datetime"),
                    pd.Index([], name="symbol"),
                ]
            )
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"], index=empty_index)

        frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        frame["datetime"] = pd.to_datetime(frame.pop("timestamp"), unit="ms", utc=True)
        frame["symbol"] = symbol
        frame = frame.set_index(["datetime", "symbol"]).sort_index()
        return validate_bars_df(frame)
