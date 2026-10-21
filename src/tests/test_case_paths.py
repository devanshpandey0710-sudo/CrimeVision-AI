"""Tests for safe case identifiers and API path containment."""

from pathlib import Path

import pytest

from utils.case_paths import case_file_path, normalize_case_id


@pytest.mark.parametrize("case_id", ["CASE-1", "Case 1", "1428", "evidence.v2"])
def test_normalize_case_id_accepts_simple_ids(case_id):
    assert normalize_case_id(case_id) == case_id


@pytest.mark.parametrize(
    "case_id",
    ["", "..", "../outside", "..\\outside", "C:\\outside", "/tmp/outside", "CON", "trailing."],
)
def test_normalize_case_id_rejects_unsafe_ids(case_id):
    assert normalize_case_id(case_id) is None


def test_normalize_case_id_rejects_non_string_values():
    assert normalize_case_id(123) is None


def test_case_file_path_stays_inside_requested_folder(tmp_path):
    result = case_file_path(tmp_path, "CASE-1", ".json")
    assert result == (Path(tmp_path) / "CASE-1.json").resolve()
    assert result.parent == Path(tmp_path).resolve()


def test_case_file_path_raises_for_unsafe_id(tmp_path):
    with pytest.raises(ValueError, match="Invalid case ID"):
        case_file_path(tmp_path, "../outside", ".json")
