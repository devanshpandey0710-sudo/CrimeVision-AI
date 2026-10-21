from services.intelligence_service import IntelligenceService


def test_audio_event_timestamps_come_from_source_segments(monkeypatch):
    service = IntelligenceService.__new__(IntelligenceService)
    service._client = object()
    monkeypatch.setattr(
        service,
        "complete",
        lambda *args, **kwargs: '{"events":[{"segment_index":1,"description":"A candidate mention","category":"statement","excerpt":"meet at noon","timestamp_start":999}]}',
    )

    result = service.extract_audio_events(
        [{"start": 12.25, "end": 14.5, "text": "They said meet at noon."}],
        "evidence-1",
    )

    assert result["status"] == "ok"
    assert result["events"][0]["timestamp_start"] == 12.25
    assert result["events"][0]["timestamp_end"] == 14.5
    assert "uncertainty" in result["events"][0]


def test_audio_event_rejects_excerpt_not_in_source_segment(monkeypatch):
    service = IntelligenceService.__new__(IntelligenceService)
    service._client = object()
    monkeypatch.setattr(
        service,
        "complete",
        lambda *args, **kwargs: '{"events":[{"segment_index":1,"description":"Claim","category":"statement","excerpt":"not spoken"}]}',
    )

    result = service.extract_audio_events(
        [{"start": 1, "end": 2, "text": "Original transcript."}], "evidence-1"
    )

    assert result["events"] == []


def test_audio_event_unavailable_does_not_call_external_service():
    service = IntelligenceService.__new__(IntelligenceService)
    service._client = None

    result = service.extract_audio_events(
        [{"start": 1, "end": 2, "text": "Transcript."}], "evidence-1"
    )

    assert result["status"] == "unavailable"
    assert result["events"] == []


def test_video_classification_copies_source_timestamp_and_requires_excerpt(monkeypatch):
    service = IntelligenceService.__new__(IntelligenceService)
    service._client = object()
    monkeypatch.setattr(
        service,
        "complete",
        lambda *args, **kwargs: '{"classifications":[{"source_reference":"frame_0001","category":"scene change","rationale":"A frame difference was recorded.","evidence_excerpt":"Frame-difference motion change"}]}',
    )
    result = service.classify_video_events(
        [{
            "source_reference": "frame_0001",
            "timestamp_start": 4.0,
            "timestamp_end": 4.0,
            "event_type": "video_motion_change",
            "description": "Frame-difference motion change at 00:00:04.",
        }],
        "video-1",
    )
    assert result["status"] == "ok"
    assert result["classifications"][0]["timestamp_start"] == 4.0
    assert "Not a finding of criminal activity" in result["classifications"][0]["uncertainty"]


def test_video_classification_unavailable_without_groq():
    service = IntelligenceService.__new__(IntelligenceService)
    service._client = None
    result = service.classify_video_events([], "video-1")
    assert result["status"] == "unavailable"
    assert result["classifications"] == []


def test_image_hypotheses_accept_only_cited_source_excerpts(monkeypatch):
    service = IntelligenceService.__new__(IntelligenceService)
    service._client = object()
    monkeypatch.setattr(
        service,
        "complete",
        lambda *args, **kwargs: '{"summary":"A doorway is recorded.","summary_event_ids":["event-1"],"hypotheses":[{"text":"A person may have entered.","supporting_event_ids":["event-1"],"evidence_excerpt":"Doorway visible","uncertainty":"The image does not establish entry."},{"text":"Unsupported claim.","supporting_event_ids":["event-1"],"evidence_excerpt":"No such source text","uncertainty":"Unclear."}]}',
    )
    result = service.generate_image_hypotheses(
        [{"event_id": "event-1", "event_type": "scene_description", "description": "Doorway visible", "uncertainty": "Machine caption"}],
        "evidence-1",
    )
    assert result["status"] == "ok"
    assert len(result["hypotheses"]) == 1
    assert result["hypotheses"][0]["supporting_event_ids"] == ["event-1"]
    assert result["hypotheses"][0]["interpretation_type"] == "tentative_llm_hypothesis"


def test_image_hypotheses_unavailable_without_groq():
    service = IntelligenceService.__new__(IntelligenceService)
    service._client = None
    result = service.generate_image_hypotheses([], "evidence-1")
    assert result["status"] == "unavailable"
    assert result["hypotheses"] == []
