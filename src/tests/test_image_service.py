"""
tests/test_image_service.py
───────────────────────────
Unit tests for image service utilities.
No model downloads required – models are mocked.
"""

import pytest
from pathlib import Path
from utils.evidence_schema import make_observation, validate_observation
from utils.timestamp_utils import seconds_to_hms, hms_to_seconds, format_duration
from utils.file_utils import allowed_image, allowed_audio, allowed_video


# ── Evidence schema tests ─────────────────────────────────────────────────────

def test_make_observation_required_fields():
    obs = make_observation(
        case_id="case-1",
        source_evidence_id="ev-1",
        modality="image",
        event_type="object_detection",
        description="Person detected",
    )
    assert obs["case_id"] == "case-1"
    assert obs["modality"] == "image"
    assert "event_id" in obs
    assert "created_at" in obs


def test_validate_observation_valid():
    obs = make_observation(
        case_id="c1", source_evidence_id="e1",
        modality="image", event_type="scene",
        description="Empty room",
    )
    ok, errors = validate_observation(obs)
    assert ok
    assert errors == []


def test_validate_observation_missing_fields():
    ok, errors = validate_observation({"modality": "image"})
    assert not ok
    assert any("case_id" in e for e in errors)


def test_validate_observation_bad_modality():
    obs = make_observation(
        case_id="c1", source_evidence_id="e1",
        modality="satellite",  # invalid
        event_type="scene", description="desc",
    )
    ok, errors = validate_observation(obs)
    assert not ok


def test_validate_observation_bad_confidence():
    obs = {
        "case_id": "c1", "source_evidence_id": "e1",
        "modality": "image", "event_type": "x",
        "description": "d", "confidence": 1.5,  # out of range
    }
    ok, errors = validate_observation(obs)
    assert not ok


def test_image_models_are_local_only_by_default(monkeypatch):
    import sys
    from types import ModuleType

    from config import Config
    from services.image_service import ImageService

    calls = []

    class FakeModel:
        def eval(self):
            return None

    class FakeLoader:
        @classmethod
        def from_pretrained(cls, model_name, **kwargs):
            calls.append((model_name, kwargs))
            return FakeModel()

    fake_transformers = ModuleType("transformers")
    for name in (
        "RTDetrForObjectDetection", "RTDetrImageProcessor",
        "BlipForConditionalGeneration", "BlipProcessor",
        "CLIPModel", "CLIPProcessor",
    ):
        setattr(fake_transformers, name, FakeLoader)
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    monkeypatch.setattr(Config.models, "ALLOW_MODEL_DOWNLOADS", False)
    monkeypatch.setattr(Config.models, "ENABLE_BLIP", True)
    monkeypatch.setattr(Config.models, "ENABLE_CLIP", True)

    status = ImageService().load_models()

    assert status == {"rtdetr": True, "blip": True, "clip": True}
    assert len(calls) == 6
    assert all(kwargs["local_files_only"] is True for _, kwargs in calls)


# ── Timestamp utils ───────────────────────────────────────────────────────────

def test_seconds_to_hms_basic():
    assert seconds_to_hms(3661.5) == "01:01:01.500"


def test_seconds_to_hms_none():
    assert seconds_to_hms(None) == "unknown"


def test_seconds_to_hms_zero():
    assert seconds_to_hms(0) == "00:00:00.000"


def test_hms_to_seconds_basic():
    assert hms_to_seconds("01:01:01.500") == pytest.approx(3661.5)


def test_hms_to_seconds_unknown():
    assert hms_to_seconds("unknown") is None


def test_hms_to_seconds_invalid():
    assert hms_to_seconds("not-a-time") is None


def test_format_duration_hours():
    assert format_duration(3723) == "1h 2m 3s"


def test_format_duration_minutes():
    assert format_duration(154) == "2m 34s"


def test_format_duration_seconds():
    assert format_duration(45) == "45s"


def test_format_duration_none():
    assert format_duration(None) == "unknown"


# ── File extension validation ─────────────────────────────────────────────────

def test_allowed_image_valid():
    assert allowed_image("photo.jpg")
    assert allowed_image("scene.PNG")
    assert allowed_image("evidence.webp")


def test_allowed_image_invalid():
    assert not allowed_image("document.pdf")
    assert not allowed_image("video.mp4")
    assert not allowed_image("script.py")


def test_allowed_audio_valid():
    assert allowed_audio("recording.wav")
    assert allowed_audio("interview.mp3")
    assert allowed_audio("audio.flac")


def test_allowed_audio_invalid():
    assert not allowed_audio("photo.jpg")
    assert not allowed_audio("video.avi")


def test_allowed_video_valid():
    assert allowed_video("footage.mp4")
    assert allowed_video("cctv.avi")
    assert allowed_video("clip.mkv")


def test_allowed_video_invalid():
    assert not allowed_video("photo.png")
    assert not allowed_video("audio.mp3")


# ── ImageService Pipeline Tests (Phase 3) ──────────────────────────────────────

def test_image_service_singleton():
    from services.image_service import ImageService, image_service
    assert image_service is ImageService.get_instance()


def test_image_service_analyse_missing_file():
    from services.image_service import image_service
    res = image_service.analyse(Path("non_existent_file.jpg"), "case-x", "ev-x")
    assert res["status"] == "error"
    assert "not found" in res["error"]


def test_image_service_rejects_corrupt_image(tmp_path):
    from services.image_service import image_service

    corrupt_path = tmp_path / "corrupt.jpg"
    corrupt_path.write_bytes(b"not a decodable image")
    result = image_service.analyse(corrupt_path, "CASE-CORRUPT", "EV-CORRUPT")

    assert result["status"] == "error"
    assert result["error"] == "The uploaded file is not a valid, readable image."


def test_annotated_image_writer_does_not_overwrite_existing_file(tmp_path, monkeypatch):
    from PIL import Image
    from config import Config
    from services.image_service import ImageService
    import uuid

    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    evidence_id = str(uuid.uuid4())
    detections = [{"label": "person", "confidence": 0.9, "box": [1, 1, 8, 8]}]
    url = ImageService._save_annotated_image(Image.new("RGB", (12, 12)), detections, evidence_id)
    output = tmp_path / f"annotated_{evidence_id}.jpg"

    assert url == f"/api/image/annotated/{evidence_id}"
    original_bytes = output.read_bytes()
    assert Image.open(output).size == (12, 12)
    assert ImageService._save_annotated_image(Image.new("RGB", (12, 12)), detections, evidence_id) is None
    assert output.read_bytes() == original_bytes


def test_heuristic_regions_are_not_reported_as_object_detections(tmp_path, monkeypatch):
    from config import Config
    from services.image_service import image_service
    from PIL import Image

    monkeypatch.setattr(Config, "DATA_FOLDER", tmp_path / "case-data")
    image_path = tmp_path / "scene.png"
    Image.new("RGB", (40, 30), color="gray").save(image_path)
    monkeypatch.setattr(
        image_service,
        "_detect_objects",
        lambda _image: ([{
            "label": "salient_foreground_entity",
            "confidence": 0.72,
            "box": [1.0, 1.0, 20.0, 20.0],
            "area_pct": 30.0,
        }], "OpenCV-ContourSaliency", "heuristic_fallback"),
    )

    result = image_service.analyse(image_path, "CASE-HEURISTIC", "EV-HEURISTIC")

    assert result["status"] == "ok"
    assert result["object_count"] == 0
    assert result["detections"] == []
    assert result["candidate_regions"][0]["label"] == "salient_foreground_entity"
    assert "not identified objects" in result["candidate_regions_note"]
    assert result["candidate_scene_categories"] == result["tags"]
    assert result["scenario_hypotheses"]["status"] == "not_generated"
    assert "not verified object detections" in result["category_note"]

    from services.fusion_service import fusion_service
    observations = fusion_service.get_timeline("CASE-HEURISTIC")["observations"]
    assert len(observations) == 1
    assert observations[0]["uncertainty"]
    assert observations[0]["event_type"] == "scene_description"


def test_image_service_analyse_valid_image(tmp_path):
    from services.image_service import image_service
    from services.fusion_service import fusion_service
    from PIL import Image
    import numpy as np

    # Generate synthetic image
    img_path = tmp_path / "crime_scene_test.png"
    arr = (np.random.rand(100, 100, 3) * 255).astype(np.uint8)
    Image.fromarray(arr).save(img_path)

    case_id = "CASE-PHASE3-TEST"
    evidence_id = "EVID-PHASE3-TEST"

    result = image_service.analyse(img_path, case_id, evidence_id)
    assert result["status"] == "ok"
    assert "caption" in result
    assert "detections" in result
    assert "forensics" in result
    assert result["resolution"] == {"width": 100, "height": 100}
    assert result["observations_created"] >= 1

    # Check persistence in timeline
    timeline = fusion_service.get_timeline(case_id)
    assert timeline["total_observations"] >= 1
    fusion_service.delete_case(case_id)
