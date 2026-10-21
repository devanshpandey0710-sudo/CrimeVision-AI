"""Validation helpers for case identifiers used in local file paths."""

from __future__ import annotations

import re
from pathlib import Path


_CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}$")
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def normalize_case_id(value: object) -> str | None:
    """Return a safe, trimmed case ID, or ``None`` when it is invalid."""
    if not isinstance(value, str):
        return None

    case_id = value.strip()
    if (
        not _CASE_ID_PATTERN.fullmatch(case_id)
        or case_id in {".", ".."}
        or ".." in case_id
        or case_id.endswith((".", " "))
        or case_id.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
    ):
        return None
    return case_id


def case_file_path(folder: Path, case_id: object, suffix: str) -> Path:
    """Build a contained path for a validated case ID and file suffix."""
    safe_id = normalize_case_id(case_id)
    if safe_id is None:
        raise ValueError("Invalid case ID.")

    root = Path(folder).resolve()
    candidate = (root / f"{safe_id}{suffix}").resolve()
    if candidate.parent != root:
        raise ValueError("Invalid case ID path.")
    return candidate
