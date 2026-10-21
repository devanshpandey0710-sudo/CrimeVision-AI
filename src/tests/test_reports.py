"""
tests/test_reports.py
Unit tests for ReportService (Phase 7 + SHA-256 integrity section).
"""

from pathlib import Path
import hashlib
import pytest


def test_report_service_singleton():
    from services.report_service import ReportService
    r1 = ReportService.get_instance()
    r2 = ReportService.get_instance()
    assert r1 is r2


def test_report_service_generate_pdf(tmp_path):
    from services.report_service import report_service
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    case_id = "CASE-REPORT-TEST"
    obs1 = make_observation(
        case_id=case_id,
        source_evidence_id="ev-1",
        modality="image",
        event_type="object_detection",
        description="Detected vehicle at entry gate",
        confidence=0.92,
    )
    obs2 = make_observation(
        case_id=case_id,
        source_evidence_id="ev-2",
        modality="audio",
        event_type="speech_segment",
        description="Subject stated 'Code confirmed' at 00:01:14",
        timestamp_start=74.0,
        timestamp_end=76.5,
        confidence=0.89,
    )
    fusion_service.save_observations(case_id, [obs1, obs2])

    out = tmp_path / "forensic_report.pdf"
    result = report_service.generate(case_id, out)

    assert result["status"] == "ok"
    assert out.exists()
    assert out.stat().st_size > 1000  # valid PDF generated
    assert result["observations_included"] == 2

    fusion_service.delete_case(case_id)


def test_report_includes_all_timeline_observations(tmp_path):
    import base64
    import zlib

    from services.report_service import report_service
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    case_id = "CASE-REPORT-TRUNCATION"
    observations = [
        make_observation(
            case_id=case_id,
            source_evidence_id=f"ev-{index:02d}",
            modality="image",
            event_type="scene_description",
            description=f"Synthetic observation {index:02d}",
            metadata=(
                {"inference_engine": "Synthetic Engine", "inference_tier": "mocked_test"}
                if index == 45 else {}
            ),
        )
        for index in range(46)
    ]
    fusion_service.save_observations(case_id, observations)
    output = tmp_path / "all_observations_report.pdf"

    result = report_service.generate(case_id, output)

    assert result["status"] == "ok"
    assert result["observations_included"] == 46
    assert result["observations_omitted"] == 0
    assert fusion_service.get_timeline(case_id)["total_observations"] == 46

    pdf_bytes = output.read_bytes()
    streams = []
    position = 0
    while True:
        stream_start = pdf_bytes.find(b"stream\n", position)
        if stream_start < 0:
            break
        data_start = stream_start + len(b"stream\n")
        stream_end = pdf_bytes.find(b"endstream", data_start)
        if stream_end < 0:
            break
        try:
            encoded = pdf_bytes[data_start:stream_end].strip()
            streams.append(zlib.decompress(base64.a85decode(encoded, adobe=True)))
        except (ValueError, zlib.error):
            pass
        position = stream_end + len(b"endstream")
    assert any(b"Synthetic observation 45" in stream for stream in streams)
    assert any(b"Synthetic Engine" in stream and b"mocked_test" in stream for stream in streams)
    fusion_service.delete_case(case_id)


def test_report_has_source_linked_image_audio_and_video_summaries(tmp_path):
    import base64
    import zlib

    from services.report_service import report_service, _detected_labels
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    case_id = "CASE-REPORT-MODALITY-SUMMARIES"
    observations = [
        make_observation(
            case_id=case_id,
            source_evidence_id="evidence-image-summary",
            modality="image",
            event_type="scene_description",
            description="Visual Scene: Synthetic doorway",
        ),
        make_observation(
            case_id=case_id,
            source_evidence_id="evidence-image-summary",
            modality="image",
            event_type="object_detection",
            description="Detected person",
            detected_objects=[{"label": "person", "confidence": 0.9}],
        ),
        make_observation(
            case_id=case_id,
            source_evidence_id="evidence-audio-summary",
            modality="audio",
            event_type="speech_segment",
            description="Speech: synthetic test phrase",
            metadata={"text": "The red car is near the building."},
        ),
        make_observation(
            case_id=case_id,
            source_evidence_id="evidence-video-summary",
            modality="video",
            event_type="video_keyframe_detection",
            description="Video frame: detected vehicle",
            detected_objects=[{"label": "vehicle", "confidence": 0.8}],
        ),
        make_observation(
            case_id=case_id,
            source_evidence_id="evidence-video-summary",
            modality="video",
            event_type="video_motion_change",
            description="Heuristic frame difference; not an action classification.",
        ),
    ]
    assert _detected_labels([observations[1]]) == {"person": 1}
    assert _detected_labels([observations[3]]) == {"vehicle": 1}
    fusion_service.save_observations(case_id, observations)
    output = tmp_path / "modality_summaries_report.pdf"

    result = report_service.generate(case_id, output)

    assert result["status"] == "ok"
    pdf_bytes = output.read_bytes()
    streams = []
    position = 0
    while True:
        stream_start = pdf_bytes.find(b"stream\n", position)
        if stream_start < 0:
            break
        data_start = stream_start + len(b"stream\n")
        stream_end = pdf_bytes.find(b"endstream", data_start)
        if stream_end < 0:
            break
        try:
            encoded = pdf_bytes[data_start:stream_end].strip()
            streams.append(zlib.decompress(base64.a85decode(encoded, adobe=True)))
        except (ValueError, zlib.error):
            pass
        position = stream_end + len(b"endstream")
    report_text = b"\n".join(streams)
    for expected in (
        b"Image Detection and Scene Summaries",
        b"evidence-image-summary",
        b"person",
        b"Synthetic doorway",
        b"Audio Transcript Summaries",
        b"evidence-audio-summary",
        b"The red car is near the building.",
        b"Video Event Summaries",
        b"evidence-video-summary",
        b"vehicle",
    ):
        assert expected in report_text
    fusion_service.delete_case(case_id)


def test_report_hashes_included_key(tmp_path):
    """generate() return dict must include hashes_included count."""
    from services.report_service import report_service
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    case_id = "CASE-REPORT-HASH"
    fake_sha = hashlib.sha256(b"fake evidence content").hexdigest()

    obs = make_observation(
        case_id=case_id,
        source_evidence_id="ev-hash-1",
        modality="image",
        event_type="scene_description",
        description="Test scene with hash",
        confidence=0.85,
        metadata={"sha256": fake_sha, "file_name": "evidence_photo.jpg"},
    )
    fusion_service.save_observations(case_id, [obs])

    out = tmp_path / "hash_report.pdf"
    result = report_service.generate(case_id, out)

    assert result["status"] == "ok"
    assert "hashes_included" in result, "Return dict must include hashes_included"
    assert result["hashes_included"] >= 1, (
        f"Expected at least 1 hash included, got {result['hashes_included']}"
    )
    fusion_service.delete_case(case_id)


def test_report_sha256_appears_in_pdf_bytes(tmp_path):
    """SHA-256 value from observation metadata must be present in the raw PDF bytes,
    confirming it was actually rendered into the integrity section."""
    from services.report_service import report_service
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    case_id = "CASE-REPORT-SHA-BYTES"
    content = b"forensic image bytes for hash test"
    expected_hash = hashlib.sha256(content).hexdigest()

    obs = make_observation(
        case_id=case_id,
        source_evidence_id="ev-sha-bytes",
        modality="image",
        event_type="scene_description",
        description="Hash embedding test",
        confidence=0.80,
        metadata={"sha256": expected_hash, "file_name": "scene.png"},
    )
    fusion_service.save_observations(case_id, [obs])

    out = tmp_path / "sha_bytes_report.pdf"
    result = report_service.generate(case_id, out)

    assert result["status"] == "ok"
    assert result["hashes_included"] == 1
    pdf_bytes = out.read_bytes()
    import base64, zlib
    decompressed_streams = []
    position = 0
    while True:
        stream_start = pdf_bytes.find(b"stream\n", position)
        if stream_start < 0:
            break
        data_start = stream_start + len(b"stream\n")
        stream_end = pdf_bytes.find(b"endstream", data_start)
        if stream_end < 0:
            break
        stream_data = pdf_bytes[data_start:stream_end].strip()
        try:
            decompressed_streams.append(zlib.decompress(base64.a85decode(stream_data, adobe=True)))
        except (ValueError, zlib.error):
            pass
        position = stream_end + len(b"endstream")
    assert any(expected_hash[:16].encode() in stream for stream in decompressed_streams), (
        "SHA-256 digest not found in decompressed PDF content stream."
    )
    fusion_service.delete_case(case_id)


def test_report_no_sha256_in_metadata_graceful(tmp_path):
    """PDF generation must succeed with hashes_included==0 when observations
    have no sha256 metadata (legacy / stub records)."""
    from services.report_service import report_service
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    case_id = "CASE-REPORT-NO-HASH"
    obs = make_observation(
        case_id=case_id,
        source_evidence_id="ev-no-hash",
        modality="audio",
        event_type="audio_summary",
        description="Ambient noise recording without hash metadata",
        confidence=0.70,
    )
    fusion_service.save_observations(case_id, [obs])

    out = tmp_path / "no_hash_report.pdf"
    result = report_service.generate(case_id, out)

    assert result["status"] == "ok"
    assert out.exists()
    assert out.stat().st_size > 500
    assert result["hashes_included"] == 0

    fusion_service.delete_case(case_id)


def test_report_does_not_overwrite_existing_file(tmp_path):
    from services.report_service import report_service

    output = tmp_path / "existing_report.pdf"
    output.write_bytes(b"existing user report")
    result = report_service.generate("CASE-REPORT-EXISTS", output)

    assert result["status"] == "error"
    assert output.read_bytes() == b"existing user report"


def test_report_escapes_untrusted_evidence_text(tmp_path):
    from services.report_service import report_service
    from services.fusion_service import fusion_service
    from utils.evidence_schema import make_observation

    case_id = "CASE-REPORT-ESCAPE"
    obs = make_observation(
        case_id=case_id,
        source_evidence_id="ev-html",
        modality="image",
        event_type="scene_description",
        description="User text: <script>alert('x')</script>",
    )
    fusion_service.save_observations(case_id, [obs])
    output = tmp_path / "escaped_report.pdf"
    result = report_service.generate(case_id, output)
    assert result["status"] == "ok"
    assert output.exists()
    fusion_service.delete_case(case_id)
