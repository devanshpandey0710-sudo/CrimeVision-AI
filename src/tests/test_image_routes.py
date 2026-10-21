from __future__ import annotations

from app import create_app
from routes import image_routes


def test_image_hypotheses_requires_explicit_consent():
    client = create_app().test_client()
    response = client.post("/api/image/hypotheses", json={
        "case_id": "CASE-TEST-001",
        "source_evidence_id": "evidence-1",
    })
    assert response.status_code == 400
    assert response.get_json()["status"] == "confirmation_required"


def test_image_hypotheses_when_groq_unavailable_sends_nothing(monkeypatch):
    client = create_app().test_client()
    monkeypatch.setattr(image_routes.intelligence_service, "_client", None)
    monkeypatch.setattr(
        image_routes.fusion_service,
        "load_observations",
        lambda case_id: (_ for _ in ()).throw(AssertionError("must not load/send observations")),
    )
    response = client.post("/api/image/hypotheses", json={
        "case_id": "CASE-TEST-001",
        "source_evidence_id": "evidence-1",
        "allow_external": True,
    })
    assert response.status_code == 503
    assert response.get_json()["status"] == "unavailable"


def test_image_hypotheses_passes_only_matching_image_observations(monkeypatch):
    client = create_app().test_client()
    monkeypatch.setattr(image_routes.intelligence_service, "_client", object())
    observations = [
        {"source_evidence_id": "evidence-1", "modality": "image", "event_id": "img-1", "description": "Doorway visible"},
        {"source_evidence_id": "evidence-2", "modality": "image", "event_id": "img-2", "description": "Other image"},
        {"source_evidence_id": "evidence-1", "modality": "audio", "event_id": "aud-1", "description": "Transcript"},
    ]
    monkeypatch.setattr(image_routes.fusion_service, "load_observations", lambda case_id: observations)
    seen = {}

    def fake_generate(selected, evidence_id):
        seen["selected"] = selected
        seen["evidence_id"] = evidence_id
        return {"status": "ok", "summary": "A doorway is recorded.", "hypotheses": [], "warning": "Tentative"}

    monkeypatch.setattr(image_routes.intelligence_service, "generate_image_hypotheses", fake_generate)
    response = client.post("/api/image/hypotheses", json={
        "case_id": "CASE-TEST-001",
        "source_evidence_id": "evidence-1",
        "allow_external": True,
    })
    assert response.status_code == 200
    assert [item["event_id"] for item in seen["selected"]] == ["img-1"]
    assert seen["evidence_id"] == "evidence-1"
