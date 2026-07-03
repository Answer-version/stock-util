from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from quantvibe.core.types import AssetType, FreqType, PriceAdjustType


class BaseProvider(ABC):
    asset_type: AssetType
    provider_name: str

    @abstractmethod
    def get_bars(
        self,
        symbols: list[str],
        freq: FreqType,
        start: str,
        end: str | None = None,
        adjust: PriceAdjustType = "raw",
    ) -> pd.DataFrame:
        """
        Return a normalized MultiIndex bars dataframe:
        index = [datetime, symbol]
        columns = [open, high, low, close, volume]
        """

    @abstractmethod
    def get_universe(
        self,
        as_of: str,
        universe_name: str | None = None,
    ) -> pd.DataFrame:
        """Return a point-in-time tradable universe snapshot."""

    def get_fundamentals(
        self,
        symbols: list[str],
        as_of: str,
        fields: list[str],
    ) -> pd.DataFrame:
        raise NotImplementedError(f"{self.provider_name} does not support fundamentals")
