"""
utils/timestamp_utils.py
────────────────────────
Helpers for converting, formatting, and sorting timestamps used across
the CrimeVision AI analysis pipeline.

Timestamps within this project can be:
  - Seconds relative to a media file (float, e.g. 12.5)
  - ISO-8601 wall-clock strings (from real-world events or report times)
  - None (unknown / unavailable)

The helper functions below handle all three cases safely.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional


def seconds_to_hms(seconds: Optional[float]) -> str:
    """
    Convert a float number of seconds to HH:MM:SS.mmm format.

    Returns "unknown" for None.

    >>> seconds_to_hms(3661.5)
    '01:01:01.500'
    >>> seconds_to_hms(None)
    'unknown'
    """
    if seconds is None:
        return "unknown"
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def hms_to_seconds(hms: str) -> Optional[float]:
    """
    Convert HH:MM:SS or HH:MM:SS.mmm string to float seconds.

    Returns None if parsing fails.

    >>> hms_to_seconds("01:01:01.500")
    3661.5
    """
    if not hms or hms.lower() == "unknown":
        return None
    try:
        parts = hms.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(hms)
    except (ValueError, TypeError):
        return None


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def sort_key(timestamp_start: Optional[float]) -> float:
    """
    Return a sort key for an observation's timestamp_start.

    Observations without a timestamp sort to the end.
    """
    return timestamp_start if timestamp_start is not None else float("inf")


def format_duration(seconds: Optional[float]) -> str:
    """
    Human-readable duration string, e.g. '2m 34s', '45s', '1h 3m'.

    Returns 'unknown' for None.
    """
    if seconds is None:
        return "unknown"
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def safe_timestamp_label(ts: Optional[float], prefix: str = "") -> str:
    """
    Return a display label for a timestamp.

    Example: "@ 00:01:23.000"  or  "@ unknown"
    """
    label = f"@ {seconds_to_hms(ts)}"
    return f"{prefix} {label}".strip() if prefix else label
