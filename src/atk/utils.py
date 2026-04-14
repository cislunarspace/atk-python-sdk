"""
Shared utilities for ATK Python SDK.
"""

from __future__ import annotations

import re
import warnings
from datetime import datetime
from typing import Callable

# ----------------------------------------------------------------------
# Time string parsing
# ----------------------------------------------------------------------

# ATK time formats observed in documentation and Connect command responses.
# Examples: "5 Nov 2022 00:00:00.000", "5 Nov 2022", "Jan 2000"
_ATK_TIME_FORMATS = [
    "%d %b %Y %H:%M:%S.%f",
    "%d %b %Y %H:%M:%S",
    "%d %b %Y",
    "%b %Y",
]

_R_DATE_STRICT = re.compile(
    r'^(\d{1,2})\s+(\w+)\s+(\d{4})\s+(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)$'
)
_R_DATE_SHORT = re.compile(r'^(\d{1,2})\s+(\w+)\s+(\d{4})$')
_R_DATETIME_COMPACT = re.compile(
    r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?$'
)

# Month name to number
_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_atk_time(time_str: str) -> datetime:
    """
    Parse an ATK time string into a Python ``datetime``.

    Supported formats (all assumed UTC):
    - ``"5 Nov 2022 00:00:00.000"``
    - ``"5 Nov 2022"``
    - ``"5 Nov 2022 00:00:00"``

    Raises ``ATKValueError`` if the string cannot be parsed.
    """
    s = time_str.strip()
    if not s:
        raise ATKValueError(f"Empty time string")

    # Try compact ISO-like format first
    m = _R_DATETIME_COMPACT.match(s)
    if m:
        year, month, day, hour, minute, sec = m.groups()
        return datetime(int(year), int(month), int(day),
                        int(hour), int(minute), int(float(sec)))

    # Try "5 Nov 2022 HH:MM:SS.mmm"
    m = _R_DATE_STRICT.match(s)
    if m:
        day, mon_str, year, hms = m.groups()
        mon = _MONTH_MAP.get(mon_str.lower())
        if mon is None:
            raise ATKValueError(f"Unknown month: {mon_str}")
        parts = hms.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        sec = float(parts[2])
        return datetime(int(year), mon, int(day), hour, minute, int(sec), int((sec % 1) * 1e6))

    # Try "5 Nov 2022"
    m = _R_DATE_SHORT.match(s)
    if m:
        day, mon_str, year = m.groups()
        mon = _MONTH_MAP.get(mon_str.lower())
        if mon is None:
            raise ATKValueError(f"Unknown month: {mon_str}")
        return datetime(int(year), mon, int(day))

    # Fallback: let datetime try its formats
    for fmt in _ATK_TIME_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    raise ATKValueError(f"Unrecognized time format: {time_str!r}")


def format_atk_time(dt: datetime) -> str:
    """
    Format a Python ``datetime`` as an ATK time string: ``"5 Nov 2022 00:00:00.000"``.
    """
    return dt.strftime("%d %b %Y %H:%M:%S.%f").rstrip("0").rstrip(".")


# ----------------------------------------------------------------------
# Path utilities
# ----------------------------------------------------------------------

def resolve_path(path: str, default_root: str = "*") -> str:
    """
    Ensure a path starts with ``*`` (scene root wildcard).

    >>> resolve_path("*/Satellite/Sat1")
    '*/Satellite/Sat1'
    >>> resolve_path("Satellite/Sat1")
    '*/Satellite/Sat1'
    >>> resolve_path("/Satellite/Sat1")
    '*/Satellite/Sat1'
    """
    path = path.strip()
    if not path.startswith("*"):
        if path.startswith("/"):
            return f"*{path}"
        return f"*/{path}"
    return path


def path_join(*parts: str) -> str:
    """
    Join ATK object path components.

    >>> path_join("*", "Satellite", "Sat1")
    '*/Satellite/Sat1'
    >>> path_join("*/Scenario/Sc1", "Satellite", "Sat1")
    '*/Scenario/Sc1/Satellite/Sat1'
    """
    joined = "/".join(parts)
    # Normalise: collapse double slashes
    while "//" in joined:
        joined = joined.replace("//", "/")
    # Ensure path starts with */
    if not joined.startswith("*"):
        joined = "*/" + joined.lstrip("/")
    return joined


def path_parent(path: str) -> str:
    """Return the parent path (everything up to the last slash)."""
    if "/" not in path:
        return "*"
    return "/".join(path.rsplit("/", 1)[:-1]) or "*"


def path_name(path: str) -> str:
    """Return the last component of a path (the object name)."""
    return path.rsplit("/", 1)[-1]


# ----------------------------------------------------------------------
# CMDRESULT parsing helpers
# ----------------------------------------------------------------------

def result_to_list(result) -> list[str]:
    """
    Convert a ``CMDRESULT`` SWIG wrapper into a plain list of strings.

    The ``CMDRESULT.m_vectData`` field is a whitespace-joined string
    (e.g. ``"val1 val2 val3"``), and ``CMDRESULT.Item(i)`` provides
    zero-based indexed access.
    """
    if result is None:
        return []
    if hasattr(result, "m_vectData") and result.m_vectData:
        # m_vectData may be a string or already a list
        data = result.m_vectData
        if isinstance(data, str):
            return data.split()
        return list(data)
    return []


def result_to_dict(result, keys: list[str]) -> dict[str, str]:
    """
    Convert a ``CMDRESULT`` into a ``dict`` using ``keys`` for column names.

    Raises ``ATKValueError`` if the result length does not match key length.
    """
    values = result_to_list(result)
    if len(values) != len(keys):
        raise ATKValueError(
            f"Result has {len(values)} values but expected {len(keys)}: {values}"
        )
    return dict(zip(keys, values))


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------

def validate_name(name: str) -> str:
    """
    Validate and sanitise an ATK object name.

    Object names must be non-empty, max 64 chars, and contain no
    characters that are special in ATK paths (``/``, ``*``, ``:``).
    """
    if not name or not name.strip():
        raise ATKValueError("Object name must be non-empty")
    if len(name) > 64:
        raise ATKValueError(f"Object name exceeds 64 characters: {name!r}")
    invalid = set("/*:")
    bad = invalid.intersection(name)
    if bad:
        raise ATKValueError(f"Object name contains invalid characters {bad}: {name!r}")
    return name.strip()


# ----------------------------------------------------------------------
# Re-export ATKValueError for use in utils
# ----------------------------------------------------------------------
from atk.exceptions import ATKValueError
