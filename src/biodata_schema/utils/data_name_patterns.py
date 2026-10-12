"""Regular expressions and helpers for data asset naming conventions."""

from datetime import datetime
from enum import Enum


class RegexParts(str, Enum):
    """Regular expression components for data asset timestamps."""

    DATE = r"\d{8}"
    TIME = r"\d{6}"
    DATETIME = r"\d{8}T\d{6}[+-]\d{4}"


class DataRegex(str, Enum):
    """Regular expression patterns for data asset names and their properties."""

    DATA = f"^(?P<label>.+?)_(?P<c_datetime>{RegexParts.DATETIME.value})$"
    DERIVED = (
        f"^(?P<input>.+?_{RegexParts.DATETIME.value})_(?P<process_name>.+?)_(?P<c_datetime>{RegexParts.DATETIME.value})"
    )
    ANALYZED = f"^(?P<project_abbreviation>.+?)_(?P<analysis_name>.+?)_(?P<c_datetime>{RegexParts.DATETIME.value})$"
    NO_UNDERSCORES = r"^[^_]+$"
    NO_SPECIAL_CHARS_EXCEPT_SPACE = r'^[^<>:;"/|?\\_]+$'


def datetime_to_name_string(dt: datetime) -> str:
    """Format a folder-safe ISO timestamp; naive datetimes use the local timezone."""
    if dt.utcoffset() is None:
        dt = dt.astimezone()
    offset = dt.utcoffset()
    if offset is not None and offset.total_seconds() % 60:
        raise ValueError("Data asset timestamps require a timezone offset in whole minutes")
    date, time = dt.isoformat(timespec="seconds").split("T")
    return f"{date.replace('-', '')}T{time.replace(':', '')}"


def datetime_from_name_string(dt: str) -> datetime:
    """Parse a folder-safe ISO timestamp, e.g. '20201229T100459+0000'."""
    return datetime.strptime(dt, "%Y%m%dT%H%M%S%z")


def build_data_name(label: str, creation_datetime: datetime) -> str:
    """Construct a data asset name from a label and creation datetime."""
    dt_str = datetime_to_name_string(creation_datetime)
    return f"{label}_{dt_str}"
