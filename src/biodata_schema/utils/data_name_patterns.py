"""Regular expressions and helpers for data asset naming conventions."""

from datetime import datetime
from enum import Enum


class RegexParts(str, Enum):
    """Regular expression components for data asset timestamps."""

    DATE = r"\d{8}"
    TIME = r"\d{6}"
    DATETIME = r"\d{8}T\d{6}[+-]\d{4}"
    LEGACY_DATETIME = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"


TIMESTAMP_PATTERN = f"(?:{RegexParts.DATETIME.value}|{RegexParts.LEGACY_DATETIME.value})"


class DataRegex(str, Enum):
    """Regular expression patterns for data asset names and their properties."""

    DATA = f"^(?P<label>.+?)_(?P<c_datetime>{TIMESTAMP_PATTERN})$"
    DERIVED = f"^(?P<input>.+?_{TIMESTAMP_PATTERN})_(?P<process_name>.+?)_(?P<c_datetime>{TIMESTAMP_PATTERN})$"
    ANALYZED = f"^(?P<project_abbreviation>.+?)_(?P<analysis_name>.+?)_(?P<c_datetime>{TIMESTAMP_PATTERN})$"
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
    """Parse current timestamps or timezone-naive historical asset timestamps."""
    try:
        return datetime.strptime(dt, "%Y%m%dT%H%M%S%z")
    except ValueError:
        return datetime.strptime(dt, "%Y-%m-%d_%H-%M-%S")


def build_data_name(label: str, creation_datetime: datetime) -> str:
    """Construct a data asset name from a label and creation datetime."""
    dt_str = datetime_to_name_string(creation_datetime)
    return f"{label}_{dt_str}"
