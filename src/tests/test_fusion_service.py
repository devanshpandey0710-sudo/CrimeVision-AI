"""
tests/test_fusion_service.py
────────────────────────────
Unit tests for the fusion / evidence storage layer.
"""

import json
import pytest
from pathlib import Path

from utils.evidence_schema import make_observation


@pytest.fixture
def fusion(tmp_path, monkeypatch):
    """Provide a FusionService instance writing to a temp data folder."""
    import config
    monkeypatch.setattr(config.Config, "DATA_FOLDER", tmp_path)
    # Re-import singleton so it picks up the patched path
    from services import fusion_service as fs_module
    from services.fusion_service import FusionService
    svc = FusionService()  # fresh instance for this test
    return svc


def _obs(case_id="c1", ts=None):
    return make_observation(
        case_id=case_id,
        source_evidence_id="ev-1",
        modality="image",
        event_type="test",
        description="test observation",
        timestamp_start=ts,
    )


def test_save_and_load(fusion):
    obs = _obs()
    fusion.save_observations("c1", [obs])
    loaded = fusion.load_observations("c1")
    assert len(loaded) == 1
    assert loaded[0]["description"] == "test observation"


def test_timeline_sorted(fusion):
    obs_a = _obs(ts=10.0)
    obs_b = _obs(ts=2.0)
    obs_c = _obs(ts=None)
    fusion.save_observations("c1", [obs_a, obs_b, obs_c])
    tl = fusion.get_timeline("c1")
    times = [o.get("timestamp_start") for o in tl["observations"]]
    # Timestamped observations should come before None
    assert times[0] == 2.0
    assert times[1] == 10.0
    assert times[2] is None


def test_list_cases(fusion):
    fusion.save_observations("caseA", [_obs("caseA")])
    fusion.save_observations("caseB", [_obs("caseB")])
    cases = fusion.list_cases()
    assert "caseA" in cases
    assert "caseB" in cases


def test_delete_case(fusion):
    fusion.save_observations("caseX", [_obs("caseX")])
    assert fusion.delete_case("caseX") is True
    assert fusion.load_observations("caseX") == []


def test_delete_nonexistent_case(fusion):
    assert fusion.delete_case("does-not-exist") is False


def test_load_missing_case(fusion):
    result = fusion.load_observations("no-case")
    assert result == []


def test_append_observations(fusion):
    fusion.save_observations("c2", [_obs("c2")])
    fusion.save_observations("c2", [_obs("c2"), _obs("c2")])
    loaded = fusion.load_observations("c2")
    assert len(loaded) == 1


def test_conflicting_observations_are_preserved(fusion):
    first = _obs("conflict-case", ts=3.0)
    second = _obs("conflict-case", ts=3.0)
    second["description"] = "conflicting observation"
    fusion.save_observations("conflict-case", [first, second])
    loaded = fusion.load_observations("conflict-case")
    assert {item["description"] for item in loaded} == {
        "test observation", "conflicting observation"
    }


def test_unrelated_media_timestamps_are_not_correlated(fusion):
    video = make_observation(
        case_id="c1", source_evidence_id="video-file", modality="video",
        event_type="video_motion_change", description="camera movement", timestamp_start=2.0,
    )
    audio = make_observation(
        case_id="c1", source_evidence_id="audio-file", modality="audio",
        event_type="speech_segment", description="brief spoken phrase", timestamp_start=2.5,
    )
    fusion.save_observations("c1", [video, audio])
    timeline = fusion.get_timeline("c1")
    assert timeline["correlations"] == []
    assert "not synchronized" in timeline["time_axis_note"]
    assert {item["timestamp_basis"] for item in timeline["observations"]} == {"media_relative"}
