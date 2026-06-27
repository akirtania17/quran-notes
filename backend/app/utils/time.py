"""Time utilities."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware in UTC.

    SQLite commonly returns naive datetimes; we treat those as UTC to avoid
    runtime errors when subtracting from aware UTC values.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat()

