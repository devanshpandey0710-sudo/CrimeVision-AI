"""
tests/test_app.py
─────────────────
Phase 1 tests: application startup, health endpoint, and basic routing.
"""

from __future__ import annotations

import json
import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Health endpoint ───────────────────────────────────────────────────────────

def test_health_returns_200(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_health_json_structure(client):
    r = client.get("/api/health")
    data = json.loads(r.data)
    assert data["status"] == "ok"
    assert "config" in data
    assert "application" in data


def test_health_config_keys(client):
    r = client.get("/api/health")
    cfg = json.loads(r.data)["config"]
    required_keys = {
        "whisper_model", "rtdetr_model", "groq_configured",
        "groq_model", "max_upload_mb",
    }
    assert required_keys.issubset(cfg.keys())


def test_health_no_api_key_exposed(client):
    """The health endpoint must never return the Groq API key."""
    r = client.get("/api/health")
    body = r.data.decode()
    assert "GROQ_API_KEY" not in body
    # The actual key value won't be "your_groq_api_key_here" in production,
    # but placeholder exposure would also be wrong.


# ── Dashboard ─────────────────────────────────────────────────────────────────

def test_dashboard_returns_200(client):
    r = client.get("/")
    assert r.status_code == 200


def test_cases_endpoint(client):
    r = client.get("/api/cases")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert "cases" in data
    assert isinstance(data["cases"], list)


def test_models_status_endpoint_structure(client):
    """The /api/models/status endpoint must return image, audio and llm sections."""
    r = client.get("/api/models/status")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert "image_models" in data
    assert "audio_models" in data
    assert "llm" in data
    assert "any_loaded" in data["image_models"]
    assert "whisper" in data["audio_models"]
    assert "groq_configured" in data["llm"]
    assert "groq_available" in data["llm"]


def test_models_status_no_key_exposed(client):
    """The model status endpoint must never expose the Groq API key value."""
    r = client.get("/api/models/status")
    body = r.data.decode()
    assert "GROQ_API_KEY" not in body
    assert "your_groq_api_key_here" not in body


# ── 404 handler ───────────────────────────────────────────────────────────────

def test_404_returns_json(client):
    r = client.get("/this/does/not/exist")
    assert r.status_code == 404
    data = json.loads(r.data)
    assert "error" in data


# ── Upload validation (no actual model needed) ───────────────────────────────

def test_image_upload_no_file(client):
    r = client.post("/api/image/analyse", data={"case_id": "test-case"})
    assert r.status_code == 400


def test_image_upload_no_case_id(client):
    import io
    data = {"file": (io.BytesIO(b"\xff\xd8\xff fake"), "photo.jpg")}
    r = client.post("/api/image/analyse", data=data, content_type="multipart/form-data")
    assert r.status_code == 400


def test_image_upload_bad_extension(client):
    import io
    data = {
        "case_id": "test-case",
        "file": (io.BytesIO(b"fake data"), "evidence.exe"),
    }
    r = client.post("/api/image/analyse", data=data, content_type="multipart/form-data")
    assert r.status_code == 415


def test_audio_upload_no_case_id(client):
    import io
    data = {"file": (io.BytesIO(b"fake audio"), "audio.mp3")}
    r = client.post("/api/audio/transcribe", data=data, content_type="multipart/form-data")
    assert r.status_code == 400


def test_audio_upload_bad_extension(client):
    import io
    data = {
        "case_id": "test-case",
        "file": (io.BytesIO(b"fake"), "audio.xyz"),
    }
    r = client.post("/api/audio/transcribe", data=data, content_type="multipart/form-data")
    assert r.status_code == 415


def test_audio_upload_rejects_mismatched_content(client, tmp_path, monkeypatch):
    import io
    from config import Config

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", upload_dir)
    data = {
        "case_id": "CASE-AUDIO-MISMATCH",
        "file": (io.BytesIO(b"not a wav file"), "audio.wav"),
    }
    r = client.post("/api/audio/transcribe", data=data, content_type="multipart/form-data")
    assert r.status_code == 415
    assert list(upload_dir.iterdir()) == []


@pytest.mark.parametrize(
    ("endpoint", "route_module", "service_name", "filename", "payload"),
    [
        ("/api/image/analyse", "image_routes", "image_service", "evidence.png", b"\x89PNG\r\n\x1a\nsynthetic"),
        ("/api/audio/transcribe", "audio_routes", "audio_service", "evidence.wav", b"RIFF\x00\x00\x00\x00WAVEfmt "),
        ("/api/video/analyse", "video_routes", "video_service", "evidence.mp4", b"\x00\x00\x00\x18ftypisomsynthetic"),
    ],
)
def test_analysis_routes_return_failure_status_for_service_errors(
    client, tmp_path, monkeypatch, endpoint, route_module, service_name, filename, payload
):
    import importlib
    import io
    from config import Config

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", upload_dir)
    module = importlib.import_module(f"routes.{route_module}")
    service = getattr(module, service_name)
    method_name = "transcribe" if service_name == "audio_service" else "analyse"
    monkeypatch.setattr(
        service,
        method_name,
        lambda *_args: {"status": "error", "error": "Synthetic analysis failure."},
    )

    response = client.post(
        endpoint,
        data={
            "case_id": "CASE-SERVICE-ERROR",
            "file": (io.BytesIO(payload), filename),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert response.get_json()["status"] == "error"
    assert response.get_json()["error"] == "Synthetic analysis failure."
    assert len(list(upload_dir.iterdir())) == 1


def test_audio_events_requires_valid_case_id(client):
    r = client.post("/api/audio/events", json={"source_evidence_id": "evidence-1"})
    assert r.status_code == 400


def test_audio_events_without_groq_does_not_send_transcript(client, monkeypatch):
    from services.intelligence_service import intelligence_service

    monkeypatch.setattr(intelligence_service, "_client", None)
    r = client.post(
        "/api/audio/events",
        json={"case_id": "CASE-AUDIO", "source_evidence_id": "evidence-1", "allow_external": True},
    )
    assert r.status_code == 503
    assert r.json["status"] == "unavailable"
    assert "No transcript was sent" in r.json["warning"]


def test_video_classification_without_groq_does_not_send_observations(client, monkeypatch):
    from services.intelligence_service import intelligence_service

    monkeypatch.setattr(intelligence_service, "_client", None)
    r = client.post(
        "/api/video/classify",
        json={"case_id": "CASE-VIDEO", "source_evidence_id": "evidence-1", "allow_external": True},
    )
    assert r.status_code == 503
    assert r.json["status"] == "unavailable"
    assert "No video observations were sent" in r.json["warning"]


def test_optional_media_routes_require_explicit_external_consent(client, monkeypatch):
    from services.intelligence_service import intelligence_service

    monkeypatch.setattr(intelligence_service, "_client", object())
    audio = client.post(
        "/api/audio/events",
        json={"case_id": "CASE-CONSENT", "source_evidence_id": "evidence-1"},
    )
    video = client.post(
        "/api/video/classify",
        json={"case_id": "CASE-CONSENT", "source_evidence_id": "evidence-1"},
    )
    assert audio.status_code == 400 and audio.json["status"] == "confirmation_required"
    assert video.status_code == 400 and video.json["status"] == "confirmation_required"


def test_video_upload_bad_extension(client):
    import io
    data = {
        "case_id": "test-case",
        "file": (io.BytesIO(b"fake"), "video.doc"),
    }
    r = client.post("/api/video/analyse", data=data, content_type="multipart/form-data")
    assert r.status_code == 415


def test_generated_media_routes_reject_invalid_identifiers(client):
    image_response = client.get("/api/image/annotated/../../secret")
    keyframe_response = client.get("/api/video/keyframes/../../secret/frame_0000_0s.jpg")
    assert image_response.status_code in (400, 404)
    assert keyframe_response.status_code in (400, 404)


def test_generated_media_routes_serve_only_generated_upload_outputs(client, tmp_path, monkeypatch):
    import uuid
    from config import Config

    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path)
    evidence_id = str(uuid.uuid4())
    (tmp_path / f"annotated_{evidence_id}.jpg").write_bytes(b"test jpeg bytes")
    frame_dir = tmp_path / f"frames_{evidence_id}"
    frame_dir.mkdir()
    (frame_dir / "frame_0000_0s.jpg").write_bytes(b"test frame bytes")

    image_response = client.get(f"/api/image/annotated/{evidence_id}")
    frame_response = client.get(f"/api/video/keyframes/{evidence_id}/frame_0000_0s.jpg")
    assert image_response.status_code == 200
    assert frame_response.status_code == 200


# ── Evidence endpoints ────────────────────────────────────────────────────────

def test_timeline_empty_case(client):
    r = client.get("/api/evidence/timeline/nonexistent-case-xyz")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data["total_observations"] == 0
    assert data["observations"] == []


def test_delete_nonexistent_case(client):
    r = client.delete("/api/evidence/case/nonexistent-case-xyz")
    assert r.status_code == 404


# ── Chat endpoint ─────────────────────────────────────────────────────────────

def test_chat_missing_case_id(client):
    r = client.post("/api/chat/ask", json={"question": "What happened?"})
    assert r.status_code == 400


def test_chat_endpoint_keeps_external_transmission_opt_in(client, monkeypatch):
    from services.chat_service import chat_service

    received = {}
    monkeypatch.setattr(
        chat_service,
        "ask",
        lambda case_id, question, allow_external=False: received.update({
            "case_id": case_id, "question": question, "allow_external": allow_external,
        }) or {"answer": "local test result", "sources": [], "warning": None},
    )
    response = client.post("/api/chat/ask", json={"case_id": "CASE-CHAT", "question": "What is recorded?"})

    assert response.status_code == 200
    assert received["allow_external"] is False


def test_chat_missing_question(client):
    r = client.post("/api/chat/ask", json={"case_id": "test-case"})
    assert r.status_code == 400


def test_chat_rejects_traversal_case_id(client):
    r = client.post("/api/chat/ask", json={
        "case_id": "../outside",
        "question": "What evidence is available?",
    })
    assert r.status_code == 400


def test_report_rejects_traversal_case_id(client):
    r = client.post("/api/report/generate", json={"case_id": "../outside"})
    assert r.status_code == 400


def test_report_download_route_returns_generated_pdf(tmp_path, monkeypatch):
    from config import Config
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    monkeypatch.setattr(Config, "DATA_FOLDER", tmp_path / "data")
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", tmp_path / "uploads")
    monkeypatch.setattr(Config, "REPORTS_FOLDER", tmp_path / "reports")
    case_id = "CASE-PDF-DOWNLOAD"
    observation = make_observation(
        case_id=case_id,
        source_evidence_id="SYNTHETIC-EVIDENCE-1",
        modality="image",
        event_type="scene_description",
        description="Synthetic test image only; not real evidence.",
        confidence=0.75,
        timestamp_start=0.0,
        timestamp_end=0.0,
        metadata={
            "file_name": "synthetic-image.png",
            "sha256": "a" * 64,
        },
    )
    fusion_service.save_observations(case_id, [observation])
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        generated = test_client.post(
            "/api/report/generate",
            json={"case_id": case_id},
        )
        downloaded = test_client.get(
            f"/api/report/download/{case_id}"
        )

    assert generated.status_code == 200
    assert generated.json["status"] == "ok"
    assert generated.json["observations_included"] == 1
    assert generated.json["hashes_included"] == 1
    assert downloaded.status_code == 200
    assert downloaded.mimetype == "application/pdf"
    assert "attachment" in downloaded.headers.get("Content-Disposition", "").lower()
    assert "crimevision_report_CASE-PDF-DOWNLOAD.pdf" in downloaded.headers.get(
        "Content-Disposition", ""
    )
    assert downloaded.data.startswith(b"%PDF-")


def test_api_cors_rejects_untrusted_origin(client):
    r = client.get("/api/health", headers={"Origin": "https://untrusted.example"})
    assert "Access-Control-Allow-Origin" not in r.headers


def test_api_cors_allows_local_origin(client):
    r = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5000"})
    assert r.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5000"


def test_chat_returns_answer_structure(client):
    r = client.post("/api/chat/ask", json={
        "case_id": "test-case",
        "question": "What evidence is available?",
    })
    assert r.status_code == 200
    data = json.loads(r.data)
    assert "answer" in data
    assert "sources" in data
