from __future__ import annotations

import pandas as pd

from quantvibe.core.exceptions import SchemaValidationError
from quantvibe.data.schemas import BAR_COLUMNS, BAR_INDEX_NAMES, BAR_INDEX_TZ, UNIVERSE_COLUMNS


def validate_bars_df(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.index, pd.MultiIndex):
        raise SchemaValidationError("bars dataframe index must be a MultiIndex")
    if tuple(df.index.names) != BAR_INDEX_NAMES:
        raise SchemaValidationError(f"bars index names must be {BAR_INDEX_NAMES}")
    datetime_index = df.index.get_level_values("datetime")
    if datetime_index.tz is None:
        raise SchemaValidationError("bars datetime index must be tz-aware")
    if str(datetime_index.tz) != BAR_INDEX_TZ:
        raise SchemaValidationError(f"bars datetime index must be {BAR_INDEX_TZ}")
    missing = [column for column in BAR_COLUMNS if column not in df.columns]
    if missing:
        raise SchemaValidationError(f"bars dataframe missing columns: {missing}")
    if df.index.has_duplicates:
        raise SchemaValidationError("bars dataframe contains duplicate [datetime, symbol] rows")
    if not df.index.is_monotonic_increasing:
        raise SchemaValidationError("bars dataframe index must be sorted ascending")
    return df


def validate_universe_df(df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in UNIVERSE_COLUMNS if column not in df.columns]
    if missing:
        raise SchemaValidationError(f"universe dataframe missing columns: {missing}")
    return df
