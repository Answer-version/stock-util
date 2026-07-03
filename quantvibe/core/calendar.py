from __future__ import annotations

import pandas as pd

UTC = "UTC"


def ensure_utc(ts: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(ts)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize(UTC)
    return timestamp.tz_convert(UTC)


def make_utc_index(values: list[pd.Timestamp] | pd.DatetimeIndex) -> pd.DatetimeIndex:
    index = pd.DatetimeIndex(values)
    if index.tz is None:
        return index.tz_localize(UTC)
    return index.tz_convert(UTC)
