import json

from services.chat_service import ChatService


def test_chat_is_local_by_default_and_limits_context(monkeypatch):
    from services.fusion_service import fusion_service
    from services.intelligence_service import intelligence_service

    observations = [{
        "event_id": "event-local-1",
        "source_evidence_id": "evidence-1",
        "modality": "audio",
        "event_type": "speech_segment",
        "description": "Transcript says meet near the gate.",
        "timestamp_start": 3.0,
        "timestamp_basis": "media_relative",
        "detected_objects": [],
    }]
    monkeypatch.setattr(fusion_service, "get_timeline", lambda case_id: {"observations": observations})
    monkeypatch.setattr(intelligence_service, "_client", object())
    monkeypatch.setattr(
        intelligence_service,
        "complete",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("external service called without consent")),
    )

    result = ChatService().ask("case-local-test", "What was said at the gate?", allow_external=False)

    assert "meet near the gate" in result["answer"]
    assert result["citations"][0]["event_id"] == "event-local-1"
    assert "no evidence or question was sent externally" in result["warning"]


def test_local_chat_labels_stored_observations_and_uncertainty(monkeypatch):
    from services.fusion_service import fusion_service
    from services.intelligence_service import intelligence_service

    observations = [{
        "event_id": "event-heuristic-1",
        "source_evidence_id": "evidence-heuristic-1",
        "modality": "image",
        "event_type": "scene_description",
        "description": "Visual scene with two candidate regions.",
        "uncertainty": "Heuristic regions are not identified objects.",
        "timestamp_basis": "unknown",
        "detected_objects": [],
    }]
    monkeypatch.setattr(fusion_service, "get_timeline", lambda case_id: {"observations": observations})
    monkeypatch.setattr(intelligence_service, "_client", None)

    result = ChatService().ask("case-heuristic-test", "Describe the visual scene.")

    assert "Heuristic regions are not identified objects." in result["answer"]
    assert "not independently verified facts" in result["answer"]
    assert "not semantic object detection" in result["answer"]


def test_chat_external_response_citations_are_checked(monkeypatch):
    from services.fusion_service import fusion_service
    from services.intelligence_service import intelligence_service

    observations = [{
        "event_id": "event-valid-1",
        "source_evidence_id": "evidence-2",
        "modality": "image",
        "event_type": "scene_description",
        "description": "A red vehicle appears in the scene.",
        "timestamp_basis": "unknown",
        "detected_objects": [],
    }]
    captured = {}
    monkeypatch.setattr(fusion_service, "get_timeline", lambda case_id: {"observations": observations})
    monkeypatch.setattr(intelligence_service, "_client", object())

    def fake_complete(system_prompt, user_message, **kwargs):
        captured["system"] = system_prompt
        captured["request"] = json.loads(user_message)
        return json.dumps({
            "answer": "The observation describes a red vehicle.",
            "citations": ["event-valid-1", "invented-event"],
            "alternative_hypotheses": [{
                "text": "The vehicle may be parked.",
                "supporting_event_ids": ["event-valid-1"],
                "uncertainty": "The image does not show intent.",
            }],
            "insufficient_information": False,
        })

    monkeypatch.setattr(intelligence_service, "complete", fake_complete)
    service = ChatService()
    service.ask("case-external-test", "Earlier local-only question", allow_external=False)
    result = service.ask("case-external-test", "Describe the red vehicle", allow_external=True)

    assert "untrusted data" in captured["system"]
    assert captured["request"]["evidence_observations"][0]["event_id"] == "event-valid-1"
    assert "recent_history" not in captured["request"]
    assert "Earlier local-only question" not in json.dumps(captured["request"])
    assert [c["event_id"] for c in result["citations"]] == ["event-valid-1"]
    assert len(result["alternative_hypotheses"]) == 1


def test_chat_history_is_separate_by_case(monkeypatch):
    from services.fusion_service import fusion_service
    from services.intelligence_service import intelligence_service

    def timeline(case_id):
        return {"observations": [{
            "event_id": f"event-{case_id}",
            "source_evidence_id": f"evidence-{case_id}",
            "modality": "image",
            "event_type": "scene_description",
            "description": f"Distinctive marker for {case_id}.",
            "timestamp_basis": "unknown",
            "detected_objects": [],
        }]}

    monkeypatch.setattr(fusion_service, "get_timeline", timeline)
    monkeypatch.setattr(intelligence_service, "_client", None)
    service = ChatService()
    service.ask("case-isolation-a", "Describe distinctive marker")
    service.ask("case-isolation-b", "Describe distinctive marker")

    assert service.get_history("case-isolation-a")[-1]["content"] != service.get_history("case-isolation-b")[-1]["content"]
