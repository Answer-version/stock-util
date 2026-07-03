BAR_INDEX_NAMES = ("datetime", "symbol")
BAR_COLUMNS = ("open", "high", "low", "close", "volume")
BAR_INDEX_TZ = "UTC"

UNIVERSE_COLUMNS = (
    "symbol",
    "asset_type",
    "exchange",
    "listed_at",
    "delisted_at",
    "tradable",
    "industry",
    "universe_name",
    "snapshot_at",
)

FUNDAMENTAL_COLUMNS = (
    "symbol",
    "field",
    "value",
    "report_date",
    "publish_date",
    "available_at",
    "source",
)
