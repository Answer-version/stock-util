class QuantVibeError(Exception):
    """Base error for the project."""


class DataError(QuantVibeError):
    """Base error for data failures."""


class DataSourceUnavailable(DataError):
    """Raised when an upstream provider cannot serve data."""


class SchemaValidationError(DataError):
    """Raised when normalized data violates the schema contract."""


class RateLimitError(DataError):
    """Raised when a data source signals a rate limit failure."""


class UnsupportedFreqError(DataError):
    """Raised when a provider cannot serve the requested frequency."""


class PointInTimeViolation(DataError):
    """Raised when a point-in-time assumption is broken."""
