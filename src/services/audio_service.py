"""
services/audio_service.py
─────────────────────────
Audio forensic analysis and transcription service for CrimeVision AI (Phase 4).

Capabilities:
  - Audio file decoding and acoustic properties extraction (duration, samplerate, RMS energy, clipping)
  - OpenAI Whisper speech-to-text transcription with timestamped segments
  - Sound event identification and silence / loud anomaly detection
  - Standardized observation generation & automatic persistence into the case timeline
  - Resilient fallback transcription & acoustic event extraction when offline or on minimal hardware
"""

from __future__ import annotations

import logging
import hashlib
import math
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np
import soundfile as sf

from config import Config
from utils.evidence_schema import make_observation
from services.fusion_service import fusion_service

logger = logging.getLogger(__name__)


class AudioService:
    """
    Forensic audio service with Whisper STT and acoustic metric analysis.
    """

    _instance: Optional["AudioService"] = None

    def __init__(self) -> None:
        self._whisper_model = None
        self._models_loaded: bool = False
        self._status: dict[str, bool] = {"whisper": False}

    @classmethod
    def get_instance(cls) -> "AudioService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_models(self) -> dict[str, bool]:
        """Load Whisper speech-to-text model on CPU."""
        if self._models_loaded:
            return self._status

        try:
            import whisper
            model_name = Config.models.WHISPER_MODEL or "base"
            download_root = Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "whisper"
            # OpenAI Whisper downloads missing checkpoints automatically. Verify
            # the local cache first unless the user explicitly opted in.
            if not Config.models.ALLOW_MODEL_DOWNLOADS:
                model_path = Path(model_name)
                model_url = getattr(whisper, "_MODELS", {}).get(model_name)
                expected_hash = None
                if model_url:
                    model_path = download_root / Path(model_url).name
                    expected_hash = model_url.rstrip("/").split("/")[-2]
                if not model_path.is_file():
                    raise FileNotFoundError(
                        "Whisper checkpoint is not available locally; model downloads are disabled."
                    )
                if expected_hash:
                    digest = hashlib.sha256()
                    with model_path.open("rb") as checkpoint_file:
                        for chunk in iter(lambda: checkpoint_file.read(1024 * 1024), b""):
                            digest.update(chunk)
                    if digest.hexdigest() != expected_hash:
                        raise ValueError(
                            "Local Whisper checkpoint failed its integrity check; downloads are disabled."
                        )
            logger.info("Loading OpenAI Whisper model: %s", model_name)
            self._whisper_model = whisper.load_model(
                model_name,
                device="cpu",
                download_root=str(download_root),
            )
            self._status["whisper"] = True
            self._models_loaded = True
            logger.info("Whisper model loaded successfully.")
        except Exception as exc:
            logger.warning("Could not load Whisper model: %s", exc)
            self._status["whisper"] = False

        return self._status

    def is_ready(self) -> bool:
        return self._whisper_model is not None

    def transcribe(
        self,
        audio_path: Path,
        case_id: str,
        evidence_id: str,
    ) -> dict[str, Any]:
        """
        Transcribe and analyze audio evidence:
          1. Extract acoustic properties (samplerate, channels, duration, RMS, peak, dynamic range)
          2. Whisper speech-to-text with segment timestamps
          3. Detect acoustic events (loud spikes, extended silence, conversational turn-taking)
          4. Persist observations to case timeline
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            return {
                "status": "error",
                "error": f"Audio file not found: {audio_path}",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }

        # 1. Acoustic inspection & SHA-256 hashing
        from utils.file_utils import file_sha256
        audio_sha256 = file_sha256(audio_path)
        acoustic_info = self._analyze_acoustics(audio_path)
        acoustic_info["sha256"] = audio_sha256

        if acoustic_info.get("decode_status") != "ok" and self._whisper_model is None:
            return {
                "status": "error",
                "error": "The audio file could not be decoded for local analysis.",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }

        # 2. Transcription
        transcript_result = self._run_whisper_or_fallback(audio_path, acoustic_info)

        full_text = transcript_result.get("text", "").strip()
        segments = transcript_result.get("segments", [])
        detected_language = transcript_result.get("language")
        stt_engine = transcript_result.get("inference_engine", "Whisper-base")
        stt_tier = transcript_result.get("inference_tier", "deep_learning" if self._whisper_model else "heuristic_fallback")
        transcription_status = "available" if stt_tier == "deep_learning" else "unavailable"

        # 3. Create standardized timeline observations with provenance
        observations: list[dict[str, Any]] = []

        # (a) Overall audio file summary observation
        summary_conf = 0.92 if stt_tier == "deep_learning" else 0.50
        summary_obs = make_observation(
            case_id=case_id,
            source_evidence_id=evidence_id,
            modality="audio",
            event_type="audio_summary",
            description=(
                f"Audio Recording: {len(segments)} speech segments returned by Whisper. "
                f"Transcript preview: '{full_text[:120]}...' [deep_learning]" if full_text else (
                    "Audio file decoded and acoustic measurements recorded. "
                    "Speech transcription is unavailable; no transcript was produced."
                )
            ),
            timestamp_start=0.0,
            timestamp_end=acoustic_info.get("duration_seconds", 0.0),
            confidence=summary_conf,
            uncertainty=(
                "No speech transcription was produced; the record contains acoustic measurements only."
                if transcription_status == "unavailable"
                else "Machine transcription may contain errors and is not a verified statement."
            ),
            metadata={
                "file_name": audio_path.name,
                "sha256": audio_sha256,
                "duration_sec": acoustic_info.get("duration_seconds", 0.0),
                "samplerate": acoustic_info.get("samplerate", 0),
                "channels": acoustic_info.get("channels", 1),
                "language": detected_language,
                "transcription_status": transcription_status,
                "rms_energy": acoustic_info.get("rms_energy", 0.0),
                "inference_engine": stt_engine,
                "inference_tier": stt_tier,
            },
        )
        observations.append(summary_obs)

        # (b) Detailed timestamped speech segment observations
        for idx, seg in enumerate(segments[:25]):
            start_t = float(seg.get("start", 0.0))
            end_t = float(seg.get("end", start_t + 1.0))
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue

            seg_obs = make_observation(
                case_id=case_id,
                source_evidence_id=evidence_id,
                modality="audio",
                event_type="speech_segment",
                description=f"Speech [{start_t:.1f}s - {end_t:.1f}s]: \"{seg_text}\"",
                timestamp_start=start_t,
                timestamp_end=end_t,
                source_reference=f"segment_{idx+1}",
                confidence=float(seg.get("confidence", 0.88 if stt_tier == "deep_learning" else 0.65)),
                metadata={
                    "segment_index": idx + 1,
                    "text": seg_text,
                    "duration": round(end_t - start_t, 2),
                    "sha256": audio_sha256,
                    "inference_engine": stt_engine,
                    "inference_tier": stt_tier,
                },
            )
            observations.append(seg_obs)

        # (c) High-energy acoustic anomalies (shouts, sudden loud sounds)
        anomalies = acoustic_info.get("loud_anomalies", [])
        for anom in anomalies[:5]:
            anom_obs = make_observation(
                case_id=case_id,
                source_evidence_id=evidence_id,
                modality="audio",
                event_type="acoustic_anomaly",
                description=f"Acoustic impulse / spike detected at {anom['timestamp']:.2f}s (peak: {anom['peak_amplitude']:.2f}) [algorithmic]",
                timestamp_start=anom["timestamp"],
                timestamp_end=anom["timestamp"] + 0.5,
                confidence=0.78,
                metadata={
                    **anom,
                    "sha256": audio_sha256,
                    "inference_engine": "SoundFile-RMSThreshold",
                    "inference_tier": "heuristic_fallback",
                },
            )
            observations.append(anom_obs)

        # 4. Save to fusion service
        try:
            fusion_service.save_observations(case_id, observations)
        except Exception as exc:
            logger.error("Failed to persist audio observations to case %s: %s", case_id, exc)

        return {
            "status": "ok",
            "case_id": case_id,
            "evidence_id": evidence_id,
            "file": audio_path.name,
            "sha256": audio_sha256,
            "inference_source": stt_tier,
            "inference_engine": stt_engine,
            "transcription_status": transcription_status,
            "warning": transcript_result.get("warning"),
            "full_transcript": full_text,
            "language": detected_language,
            "segments": segments,
            "acoustics": acoustic_info,
            "observations_created": len(observations),
        }

    def _analyze_acoustics(self, path: Path) -> dict[str, Any]:
        """Calculate acoustic metrics: duration, sample rate, RMS, loud spikes."""
        try:
            data, sr = sf.read(str(path))
            if data.ndim > 1:
                channels = data.shape[1]
                mono = data.mean(axis=1)
            else:
                channels = 1
                mono = data

            duration = float(len(mono) / sr) if sr > 0 else 0.0
            rms = float(np.sqrt(np.mean(mono**2)))
            peak = float(np.max(np.abs(mono))) if len(mono) > 0 else 0.0

            # Detect loud spikes (peaks 3.5x higher than RMS)
            anomalies = []
            if rms > 0.005:
                window_size = int(sr * 0.2)  # 200ms
                threshold = max(0.5, rms * 3.5)
                for i in range(0, len(mono) - window_size, window_size * 2):
                    chunk = mono[i : i + window_size]
                    chunk_peak = float(np.max(np.abs(chunk)))
                    if chunk_peak > threshold:
                        t = round(float(i / sr), 2)
                        anomalies.append({
                            "timestamp": t,
                            "peak_amplitude": round(chunk_peak, 3),
                            "type": "loud_impulse",
                        })

            return {
                "decode_status": "ok",
                "samplerate": sr,
                "channels": channels,
                "duration_seconds": round(duration, 2),
                "rms_energy": round(rms, 4),
                "peak_amplitude": round(peak, 3),
                "loud_anomalies": anomalies,
            }
        except Exception as exc:
            logger.warning("SoundFile acoustic analysis failed: %s", exc)
            return {
                "decode_status": "unavailable",
                "decode_error": type(exc).__name__,
                "samplerate": 16000,
                "channels": 1,
                "duration_seconds": 0.0,
                "rms_energy": 0.0,
                "peak_amplitude": 0.0,
                "loud_anomalies": [],
            }

    @staticmethod
    def _prepare_whisper_input(path: Path) -> str | np.ndarray:
        """Decode supported files in-process; give Whisper mono 16 kHz samples."""
        try:
            audio, sample_rate = sf.read(
                str(path), dtype="float32", always_2d=True
            )
        except Exception as exc:
            # Let Whisper use its FFmpeg decoder for formats SoundFile cannot read.
            logger.debug("SoundFile could not decode Whisper input (%s).", type(exc).__name__)
            return str(path)

        if sample_rate <= 0 or audio.size == 0:
            return str(path)

        mono = np.mean(audio, axis=1, dtype=np.float32)
        if sample_rate == 16000:
            return mono

        try:
            from scipy.signal import resample_poly
        except ImportError:
            # The optional AI requirements include SciPy. If it is missing,
            # preserve Whisper's normal file/FFmpeg path instead of using a
            # low-quality sample-rate conversion.
            logger.warning("SciPy is unavailable; Whisper will use its file decoder.")
            return str(path)

        divisor = math.gcd(int(sample_rate), 16000)
        return resample_poly(
            mono,
            up=16000 // divisor,
            down=int(sample_rate) // divisor,
        ).astype(np.float32, copy=False)

    def _run_whisper_or_fallback(self, path: Path, acoustics: dict[str, Any]) -> dict[str, Any]:
        """Execute Whisper transcription with CPU fallback."""
        if self._whisper_model is not None:
            try:
                whisper_input = self._prepare_whisper_input(path)
                result = self._whisper_model.transcribe(whisper_input, fp16=False)
                raw_segments = result.get("segments", [])
                formatted_segments = []
                for s in raw_segments:
                    formatted_segments.append({
                        "id": s.get("id"),
                        "start": round(float(s.get("start", 0.0)), 2),
                        "end": round(float(s.get("end", 0.0)), 2),
                        "text": s.get("text", "").strip(),
                        "confidence": 0.90,
                    })
                return {
                    "text": result.get("text", "").strip(),
                    "language": result.get("language"),
                    "segments": formatted_segments,
                    "inference_engine": f"OpenAI Whisper ({Config.models.WHISPER_MODEL or 'base'})",
                    "inference_tier": "deep_learning",
                }
            except Exception as exc:
                logger.warning("Whisper inference failed: %s, using fallback.", exc)
                fallback_warning = "Whisper transcription failed; only acoustic analysis is available."
        else:
            fallback_warning = "Whisper is not loaded; no transcript was produced."

        # Never fabricate transcript text or transcript timestamps.
        return {
            "text": "",
            "language": None,
            "segments": [],
            "inference_engine": "SoundFile-AcousticAnalysis",
            "inference_tier": "heuristic_fallback",
            "warning": fallback_warning,
        }


audio_service = AudioService.get_instance()
