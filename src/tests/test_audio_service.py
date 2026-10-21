"""
tests/test_audio_service.py
───────────────────────────
Unit tests for AudioService (Phase 4).
"""

from pathlib import Path
import numpy as np
import soundfile as sf
import pytest


def test_audio_service_singleton():
    from services.audio_service import AudioService
    a1 = AudioService.get_instance()
    a2 = AudioService.get_instance()
    assert a1 is a2


def test_audio_service_missing_file():
    from services.audio_service import audio_service
    res = audio_service.transcribe(Path("missing_audio.wav"), "case-1", "ev-1")
    assert res["status"] == "error"
    assert "not found" in res["error"]


def test_audio_service_transcribe_and_timeline(tmp_path):
    from services.audio_service import audio_service
    from services.fusion_service import fusion_service

    # Create synthetic test WAV file
    sample_rate = 16000
    duration_sec = 2.0
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # Generate 440 Hz tone with a spike
    audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
    audio_data[int(sample_rate * 0.5) : int(sample_rate * 0.6)] = 0.95  # loud impulse

    wav_path = tmp_path / "forensic_audio_test.wav"
    sf.write(str(wav_path), audio_data, sample_rate)

    case_id = "CASE-AUDIO-PHASE4"
    evidence_id = "EVID-AUDIO-PHASE4"

    res = audio_service.transcribe(wav_path, case_id, evidence_id)
    assert res["status"] == "ok"
    assert "full_transcript" in res
    assert "acoustics" in res
    assert res["acoustics"]["samplerate"] == sample_rate
    assert res["acoustics"]["duration_seconds"] == pytest.approx(2.0, abs=0.1)
    assert res["observations_created"] >= 1
    assert res["transcription_status"] == "unavailable"
    assert res["full_transcript"] == ""
    assert res["segments"] == []

    # Verify timeline integration
    timeline = fusion_service.get_timeline(case_id)
    assert timeline["total_observations"] >= 1
    assert any(o["modality"] == "audio" for o in timeline["observations"])
    fusion_service.delete_case(case_id)


def test_load_models_returns_dict():
    from services.audio_service import audio_service
    status = audio_service.load_models()
    assert isinstance(status, dict)
    assert "whisper" in status


def test_whisper_missing_checkpoint_does_not_download(tmp_path, monkeypatch):
    import sys
    from types import ModuleType

    from config import Config
    from services.audio_service import AudioService

    fake_whisper = ModuleType("whisper")
    fake_whisper.available_models = lambda: ["base"]
    fake_whisper.load_model = lambda *args, **kwargs: pytest.fail(
        "Whisper must not be called when its local checkpoint is missing."
    )
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(Config.models, "WHISPER_MODEL", "base")
    monkeypatch.setattr(Config.models, "ALLOW_MODEL_DOWNLOADS", False)

    service = AudioService()
    status = service.load_models()

    assert status["whisper"] is False
    assert service.is_ready() is False


def test_whisper_cached_checkpoint_loads_without_download(tmp_path, monkeypatch):
    import sys
    from types import ModuleType

    from config import Config
    from services.audio_service import AudioService

    cache_root = tmp_path / "cache"
    checkpoint = cache_root / "whisper" / "base.pt"
    checkpoint.parent.mkdir(parents=True)
    checkpoint_contents = b"synthetic checkpoint placeholder"
    checkpoint.write_bytes(checkpoint_contents)
    import hashlib
    checkpoint_hash = hashlib.sha256(checkpoint_contents).hexdigest()
    calls = []
    fake_whisper = ModuleType("whisper")
    fake_whisper._MODELS = {"base": f"https://example.invalid/{checkpoint_hash}/base.pt"}
    fake_whisper.load_model = lambda *args, **kwargs: calls.append((args, kwargs)) or object()
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_root))
    monkeypatch.setattr(Config.models, "WHISPER_MODEL", "base")
    monkeypatch.setattr(Config.models, "ALLOW_MODEL_DOWNLOADS", False)

    status = AudioService().load_models()

    assert status["whisper"] is True
    assert calls[0][1]["download_root"] == str(checkpoint.parent)


def test_unavailable_whisper_fallback_does_not_invent_transcript():
    from services.audio_service import AudioService

    service = AudioService()
    result = service._run_whisper_or_fallback(
        Path("unused.wav"), {"duration_seconds": 4.0}
    )

    assert result["text"] == ""
    assert result["language"] is None
    assert result["segments"] == []
    assert result["inference_tier"] == "heuristic_fallback"
    assert "no transcript" in result["warning"].lower()


def test_whisper_receives_decoded_wav_samples_without_ffmpeg(tmp_path, monkeypatch):
    from config import Config
    from services.audio_service import AudioService

    monkeypatch.setattr(Config, "DATA_FOLDER", tmp_path / "case-data")
    sample_rate = 16000
    audio_path = tmp_path / "speech.wav"
    sf.write(audio_path, np.zeros(sample_rate, dtype=np.float32), sample_rate)

    class FakeWhisper:
        def transcribe(self, audio, fp16):
            assert isinstance(audio, np.ndarray)
            assert audio.dtype == np.float32
            assert audio.shape == (sample_rate,)
            assert fp16 is False
            return {
                "text": "synthetic test phrase",
                "language": "en",
                "segments": [{"id": 0, "start": 0.0, "end": 1.0, "text": "synthetic test phrase"}],
            }

    service = AudioService()
    service._whisper_model = FakeWhisper()
    result = service.transcribe(audio_path, "CASE-SYNTHETIC-AUDIO", "SYNTHETIC-AUDIO-1")

    assert result["status"] == "ok"
    assert result["transcription_status"] == "available"
    assert result["full_transcript"] == "synthetic test phrase"
    assert result["segments"][0]["start"] == 0.0
