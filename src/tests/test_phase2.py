"""
tests/test_phase2.py
────────────────────
Phase 2 regression tests covering:
  1. SHA-256 evidence integrity  (Task 1)
  2. Detection provenance tags   (Task 2)
  3. Lightweight IOU entity tracking (Task 3)

No model downloads required – all heavy models are bypassed by the
existing fallback logic when weights are absent from the local cache.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image


# ── Task 1: SHA-256 integrity ──────────────────────────────────────────────────

class TestSha256Integrity:
    """file_sha256 / compute_file_sha256 round-trip tests."""

    def test_sha256_known_content(self, tmp_path):
        from utils.file_utils import file_sha256
        p = tmp_path / "known.bin"
        p.write_bytes(b"CrimeVision AI - Phase 2 Test")
        expected = hashlib.sha256(b"CrimeVision AI - Phase 2 Test").hexdigest()
        assert file_sha256(p) == expected

    def test_sha256_alias_matches(self, tmp_path):
        from utils.file_utils import file_sha256, compute_file_sha256
        p = tmp_path / "alias.bin"
        p.write_bytes(os.urandom(1024))
        assert file_sha256(p) == compute_file_sha256(p)

    def test_sha256_different_files_differ(self, tmp_path):
        from utils.file_utils import file_sha256
        p1 = tmp_path / "f1.bin"
        p2 = tmp_path / "f2.bin"
        p1.write_bytes(b"alpha")
        p2.write_bytes(b"beta")
        assert file_sha256(p1) != file_sha256(p2)

    def test_sha256_empty_file(self, tmp_path):
        from utils.file_utils import file_sha256
        p = tmp_path / "empty.bin"
        p.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert file_sha256(p) == expected

    def test_sha256_large_file_chunked(self, tmp_path):
        """Verify chunked hashing gives same result as one-shot hashlib call."""
        from utils.file_utils import file_sha256
        data = os.urandom(200 * 1024)   # 200 KB
        p = tmp_path / "large.bin"
        p.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert file_sha256(p) == expected

    def test_sha256_in_image_result(self, tmp_path):
        """Image service should embed sha256 in its return dict."""
        from services.image_service import image_service
        img = Image.fromarray(
            (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
        )
        p = tmp_path / "test_sha256_img.png"
        img.save(p)
        result = image_service.analyse(p, "CASE-SHA256-IMG", "EV-SHA256-IMG")
        assert result.get("status") == "ok", result.get("error")
        assert "sha256" in result
        assert len(result["sha256"]) == 64   # full hex digest
        # Verify it matches the file on disk
        assert result["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
        # Cleanup
        from services.fusion_service import fusion_service
        fusion_service.delete_case("CASE-SHA256-IMG")

    def test_sha256_in_audio_result(self, tmp_path):
        """Audio service should embed sha256 in its return dict."""
        from services.audio_service import audio_service
        # Minimal valid WAV: 44-byte header + silence
        p = tmp_path / "test_sha256_audio.wav"
        _write_minimal_wav(p, duration_secs=0.5)
        result = audio_service.transcribe(p, "CASE-SHA256-AUD", "EV-SHA256-AUD")
        assert result.get("status") == "ok", result.get("error")
        assert "sha256" in result
        assert len(result["sha256"]) == 64
        from services.fusion_service import fusion_service
        fusion_service.delete_case("CASE-SHA256-AUD")

    def test_sha256_in_video_result(self, tmp_path):
        """Video service should embed sha256 in its return dict."""
        from services.video_service import video_service
        p = _make_test_video(tmp_path, "sha256_test.avi", n_frames=15)
        result = video_service.analyse(p, "CASE-SHA256-VID", "EV-SHA256-VID")
        assert result.get("status") == "ok", result.get("error")
        assert "sha256" in result
        assert len(result["sha256"]) == 64
        from services.fusion_service import fusion_service
        fusion_service.delete_case("CASE-SHA256-VID")


# ── Task 2: Detection provenance ───────────────────────────────────────────────

class TestDetectionProvenance:
    """Provenance / inference_source fields are present in service outputs."""

    def test_image_provenance_field_present(self, tmp_path):
        from services.image_service import image_service
        img = Image.fromarray(
            (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
        )
        p = tmp_path / "prov_test.png"
        img.save(p)
        result = image_service.analyse(p, "CASE-PROV-IMG", "EV-PROV-IMG")
        assert result.get("status") == "ok", result.get("error")
        assert "inference_source" in result
        assert result["inference_source"] in ("deep_learning", "heuristic_fallback")
        from services.fusion_service import fusion_service
        fusion_service.delete_case("CASE-PROV-IMG")

    def test_image_provenance_in_observations(self, tmp_path):
        """At least one stored observation should carry provenance metadata."""
        from services.image_service import image_service
        from services.fusion_service import fusion_service
        img = Image.fromarray(
            (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
        )
        p = tmp_path / "prov_obs_test.png"
        img.save(p)
        image_service.analyse(p, "CASE-PROV-OBS", "EV-PROV-OBS")
        tl = fusion_service.get_timeline("CASE-PROV-OBS")
        obs_list = tl.get("observations", [])
        assert obs_list, "Expected at least one observation in timeline"
        obs = obs_list[0]
        meta = obs.get("metadata", {})
        # Provenance is stored in observation metadata dict
        has_prov = (
            "inference_source" in obs or "inference_engine" in obs
            or "inference_engine" in meta or "inference_tier" in meta
        )
        assert has_prov, (
            f"Observation missing provenance fields.\n"
            f"  Top-level keys: {list(obs.keys())}\n"
            f"  Metadata keys: {list(meta.keys())}"
        )
        fusion_service.delete_case("CASE-PROV-OBS")


    def test_audio_provenance_field_present(self, tmp_path):
        from services.audio_service import audio_service
        p = tmp_path / "prov_audio.wav"
        _write_minimal_wav(p, duration_secs=0.5)
        result = audio_service.transcribe(p, "CASE-PROV-AUD", "EV-PROV-AUD")
        assert result.get("status") == "ok", result.get("error")
        assert "inference_source" in result
        assert result["inference_source"] in ("deep_learning", "heuristic_fallback")
        from services.fusion_service import fusion_service
        fusion_service.delete_case("CASE-PROV-AUD")

    def test_provenance_source_is_string(self, tmp_path):
        """inference_source must be a non-empty string."""
        from services.image_service import image_service
        img = Image.fromarray(
            (np.random.rand(32, 32, 3) * 255).astype(np.uint8)
        )
        p = tmp_path / "prov_type.png"
        img.save(p)
        result = image_service.analyse(p, "CASE-PROV-TYPE", "EV-PROV-TYPE")
        assert isinstance(result.get("inference_source"), str)
        assert len(result["inference_source"]) > 0
        from services.fusion_service import fusion_service
        fusion_service.delete_case("CASE-PROV-TYPE")


# ── Task 3: Lightweight IOU Entity Tracking ────────────────────────────────────

class TestIouTracking:
    """Unit tests for the _calculate_iou helper and track_id assignment."""

    def test_calculate_iou_perfect_overlap(self):
        from services.video_service import VideoService
        vs = VideoService.get_instance()
        box = [10, 10, 50, 50]
        assert vs._calculate_iou(box, box) == pytest.approx(1.0)

    def test_calculate_iou_no_overlap(self):
        from services.video_service import VideoService
        vs = VideoService.get_instance()
        a = [0, 0, 10, 10]
        b = [20, 20, 30, 30]
        assert vs._calculate_iou(a, b) == pytest.approx(0.0)

    def test_calculate_iou_partial_overlap(self):
        from services.video_service import VideoService
        vs = VideoService.get_instance()
        # Box A: [0,0,10,10] area=100
        # Box B: [5,5,15,15] area=100, intersection=[5,5,10,10]=25
        # Union = 100+100-25 = 175, IoU = 25/175 ≈ 0.143
        a = [0, 0, 10, 10]
        b = [5, 5, 15, 15]
        assert vs._calculate_iou(a, b) == pytest.approx(25 / 175, rel=1e-3)

    def test_calculate_iou_contained_box(self):
        from services.video_service import VideoService
        vs = VideoService.get_instance()
        outer = [0, 0, 100, 100]
        inner = [25, 25, 75, 75]
        iou = vs._calculate_iou(outer, inner)
        # intersection = 50*50 = 2500, union = 10000 + 2500 - 2500 = 10000
        assert iou == pytest.approx(2500 / 10000)

    def test_track_ids_assigned_in_video(self, tmp_path, monkeypatch):
        """After video analysis, keyframe observations must carry detected_objects
        with a track_id field — verifies the fix is genuine, not vacuous."""
        from services.video_service import video_service
        from services.image_service import image_service
        from services.fusion_service import fusion_service
        monkeypatch.setattr(
            image_service,
            "_detect_objects",
            lambda image: ([{"label": "person", "confidence": 0.9, "box": [20, 20, 80, 80]}], "RT-DETR test double", "deep_learning"),
        )
        p = _make_test_video(tmp_path, "tracking_test.avi", n_frames=30)
        result = video_service.analyse(p, "CASE-TRACK", "EV-TRACK")
        assert result.get("status") == "ok", result.get("error")
        tl = fusion_service.get_timeline("CASE-TRACK")
        obs_list = tl.get("observations", [])
        assert obs_list, "Expected at least one observation in timeline"

        # Collect only keyframe detection observations (not the video_summary)
        keyframe_obs = [
            o for o in obs_list
            if o.get("event_type") == "video_keyframe_detection"
        ]
        assert keyframe_obs, (
            "Expected at least one video_keyframe_detection observation — "
            "the test video has 30 frames and should produce detections"
        )

        # Every keyframe detection observation must have a non-empty detected_objects
        # list with track_id present on every entry.
        for obs in keyframe_obs:
            dets = obs.get("detected_objects", [])
            assert dets, (
                f"Observation {obs.get('event_id')} has empty detected_objects. "
                "track_id is not being persisted."
            )
            for obj in dets:
                assert "track_id" in obj, (
                    f"Missing track_id in detected object: {obj}\n"
                    f"Observation: {obs.get('event_id')}"
                )
                # track_id must be a positive integer (assigned by the tracker)
                assert isinstance(obj["track_id"], int) and obj["track_id"] >= 1, (
                    f"track_id must be a positive int, got: {obj['track_id']!r}"
                )
        fusion_service.delete_case("CASE-TRACK")

    def test_video_provenance_reflects_actual_tier(self, tmp_path):
        """inference_source in the video result must be one of the two valid tiers
        and must not be hardcoded to heuristic_fallback when the fallback ran."""
        from services.video_service import video_service
        from services.fusion_service import fusion_service
        p = _make_test_video(tmp_path, "provenance_test.avi", n_frames=20)
        result = video_service.analyse(p, "CASE-VID-PROV", "EV-VID-PROV")
        assert result.get("status") == "ok", result.get("error")
        tier = result.get("inference_source")
        assert tier in ("deep_learning", "heuristic_fallback"), (
            f"inference_source must be 'deep_learning' or 'heuristic_fallback', got {tier!r}"
        )
        engine = result.get("inference_engine")
        assert isinstance(engine, str) and len(engine) > 0, (
            "inference_engine must be a non-empty string"
        )
        # Without model weights, the fallback must report heuristic_fallback honestly
        # (models are not loaded in the test environment)
        assert tier == "heuristic_fallback", (
            "In the test environment no model weights are loaded; "
            "inference_source must be 'heuristic_fallback'"
        )
        fusion_service.delete_case("CASE-VID-PROV")

    def test_video_result_has_sha256_and_provenance(self, tmp_path):
        """Smoke test: video result carries both sha256 and inference_source."""
        from services.video_service import video_service
        from services.fusion_service import fusion_service
        p = _make_test_video(tmp_path, "combo_test.avi", n_frames=12)
        result = video_service.analyse(p, "CASE-COMBO", "EV-COMBO")
        assert result.get("status") == "ok", result.get("error")
        assert "sha256" in result
        assert "inference_source" in result
        fusion_service.delete_case("CASE-COMBO")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_minimal_wav(path: Path, duration_secs: float = 0.5, sample_rate: int = 16000):
    """Write a minimal PCM WAV file with silence."""
    import struct, wave
    n_samples = int(sample_rate * duration_secs)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_samples)


def _make_test_video(tmp_path: Path, name: str, n_frames: int = 20) -> Path:
    """Create a synthetic AVI video for testing purposes."""
    video_path = tmp_path / name
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(str(video_path), fourcc, 10, (160, 120))
    for i in range(n_frames):
        frame = np.full((120, 160, 3), (i * 5) % 200, dtype=np.uint8)
        if i > n_frames // 2:
            cv2.rectangle(frame, (30, 30), (80, 80), (255, 255, 255), -1)
        out.write(frame)
    out.release()
    return video_path
