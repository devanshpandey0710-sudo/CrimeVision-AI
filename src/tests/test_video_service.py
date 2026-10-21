"""
tests/test_video_service.py
───────────────────────────
Unit tests for VideoService (Phase 5).
"""

from pathlib import Path
import cv2
import numpy as np
import pytest


def test_video_service_singleton():
    from services.video_service import VideoService
    v1 = VideoService.get_instance()
    v2 = VideoService.get_instance()
    assert v1 is v2


def test_video_service_missing_file():
    from services.video_service import video_service
    res = video_service.analyse(Path("missing_video.mp4"), "case-1", "ev-1")
    assert res["status"] == "error"
    assert "not found" in res["error"]


def test_video_service_analyse_valid_video(tmp_path):
    from services.video_service import video_service
    from services.fusion_service import fusion_service

    # Create synthetic AVI test video using OpenCV
    video_path = tmp_path / "forensic_video_test.avi"
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    width, height, fps = 160, 120, 10
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    # Write 25 frames (2.5 seconds) with simulated visual shift
    for i in range(25):
        frame = np.full((height, width, 3), (i * 8) % 255, dtype=np.uint8)
        if i > 12:
            cv2.rectangle(frame, (20, 20), (80, 80), (255, 255, 255), -1)
        out.write(frame)
    out.release()

    case_id = "CASE-VIDEO-PHASE5"
    evidence_id = "EVID-VIDEO-PHASE5"

    res = video_service.analyse(video_path, case_id, evidence_id)
    assert res["status"] == "ok"
    assert "metadata" in res
    assert res["metadata"]["width"] == width
    assert res["metadata"]["height"] == height
    assert res["keyframes_extracted"] >= 1
    assert res["observations_created"] >= 1
    assert all("frame_index" in frame and "timestamp" in frame for frame in res["keyframes"])

    # Verify timeline integration
    timeline = fusion_service.get_timeline(case_id)
    assert timeline["total_observations"] >= 1
    assert any(o["modality"] == "video" for o in timeline["observations"])
    fusion_service.delete_case(case_id)


def test_video_motion_change_is_a_tentative_timeline_observation(tmp_path):
    from services.video_service import video_service
    from services.fusion_service import fusion_service

    video_path = tmp_path / "motion_video.avi"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for value in ([0] * 15 + [255] * 15):
        writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
    writer.release()

    result = video_service.analyse(video_path, "CASE-VID-MOTION", "EV-VID-MOTION")
    assert result["status"] == "ok"
    timeline = fusion_service.get_timeline("CASE-VID-MOTION")
    motion = [o for o in timeline["observations"] if o.get("event_type") == "video_motion_change"]
    assert motion
    assert motion[0]["timestamp_start"] == motion[0]["timestamp_end"]
    assert "not an action classification" in motion[0]["description"]
    fusion_service.delete_case("CASE-VID-MOTION")


def test_video_service_handles_corrupt_container(tmp_path):
    from services.video_service import video_service

    video_path = tmp_path / "corrupt.avi"
    video_path.write_bytes(b"RIFF" + b"not a valid video" * 10)
    result = video_service.analyse(video_path, "CASE-VID-CORRUPT", "EV-VID-CORRUPT")
    assert result["status"] == "error"


def test_video_fallback_regions_are_not_reported_as_object_detections(tmp_path, monkeypatch):
    from services.video_service import video_service
    from services.image_service import image_service
    from services.fusion_service import fusion_service

    video_path = tmp_path / "fallback_video.avi"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 5, (64, 48))
    for _ in range(12):
        writer.write(np.full((48, 64, 3), 100, dtype=np.uint8))
    writer.release()
    monkeypatch.setattr(
        image_service,
        "_detect_objects",
        lambda image: ([{"label": "candidate_region", "confidence": 0.7, "box": [1, 1, 20, 20]}], "OpenCV test fallback", "heuristic_fallback"),
    )

    result = video_service.analyse(video_path, "CASE-VID-FALLBACK", "EV-VID-FALLBACK")

    assert result["status"] == "ok"
    assert result["keyframes"][0]["detections_count"] == 0
    assert result["keyframes"][0]["candidate_regions_count"] == 1
    timeline = fusion_service.get_timeline("CASE-VID-FALLBACK")
    assert not any(item.get("event_type") == "video_keyframe_detection" for item in timeline["observations"])
    fusion_service.delete_case("CASE-VID-FALLBACK")


def test_video_pixel_limit_rejects_before_frame_decode(tmp_path, monkeypatch):
    from config import Config
    from services.video_service import video_service

    video_path = tmp_path / "pixel_limit.avi"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 5, (64, 48))
    writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
    writer.release()
    monkeypatch.setattr(Config.video, "MAX_FRAME_PIXELS", 100)

    result = video_service.analyse(video_path, "CASE-VID-LIMIT", "EV-VID-LIMIT")

    assert result["status"] == "error"
    assert "pixel limit" in result["error"]


def test_load_models_returns_dict():
    from services.video_service import video_service
    status = video_service.load_models()
    assert isinstance(status, dict)
    assert "video_extractor" in status
