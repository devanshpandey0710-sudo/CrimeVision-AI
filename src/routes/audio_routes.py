"""
routes/audio_routes.py
──────────────────────
Audio upload and transcription endpoints.
Full implementation in Phase 4.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from config import Config
from utils.file_utils import allowed_audio, safe_save, sniff_magic
from services.audio_service import audio_service
from services.fusion_service import fusion_service
from services.intelligence_service import intelligence_service
from utils.case_paths import normalize_case_id

logger = logging.getLogger(__name__)
audio_bp = Blueprint("audio", __name__, url_prefix="/api/audio")


@audio_bp.route("/transcribe", methods=["POST"])
def transcribe_audio():
    """
    Upload and transcribe an audio file.

    Form fields:
      file     – audio file (required)
      case_id  – case identifier (required)
    """
    case_id = normalize_case_id(request.form.get("case_id"))
    if not case_id:
        return jsonify({"error": "A valid case_id is required."}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected."}), 400

    if not allowed_audio(file.filename):
        return jsonify({
            "error": f"Unsupported audio format. "
                     f"Allowed: {', '.join(sorted(Config.ALLOWED_AUDIO_EXT))}."
        }), 415

    try:
        evidence_id, saved_path = safe_save(file, Config.UPLOAD_FOLDER)
    except (ValueError, OSError) as exc:
        logger.error("Audio save failed: %s", exc)
        return jsonify({"error": f"Could not save file: {exc}"}), 500

    ext = saved_path.suffix.lstrip(".").lower()
    if not sniff_magic(saved_path, ext):
        saved_path.unlink(missing_ok=True)
        return jsonify({"error": "File content does not match its audio extension."}), 415

    result = audio_service.transcribe(saved_path, case_id, evidence_id)
    if result.get("status") == "error":
        return jsonify(result), 422
    return jsonify(result)


@audio_bp.route("/events", methods=["POST"])
def extract_audio_events():
    """Explicitly send stored transcript text to Groq for candidate events."""
    body = request.get_json(silent=True) or {}
    case_id = normalize_case_id(body.get("case_id"))
    evidence_id = body.get("source_evidence_id")
    if not case_id:
        return jsonify({"error": "A valid case_id is required."}), 400
    if not isinstance(evidence_id, str) or not evidence_id.strip() or len(evidence_id) > 128:
        return jsonify({"error": "A valid source_evidence_id is required."}), 400
    if body.get("allow_external") is not True:
        return jsonify({
            "status": "confirmation_required",
            "events": [],
            "warning": "Set allow_external=true only after confirming that transcript text may be sent.",
        }), 400
    if not intelligence_service.is_available:
        return jsonify({
            "status": "unavailable",
            "events": [],
            "warning": "Groq is not configured. No transcript was sent.",
        }), 503

    observations = fusion_service.load_observations(case_id)
    segments = []
    for observation in observations:
        if (
            observation.get("source_evidence_id") == evidence_id
            and observation.get("event_type") == "speech_segment"
            and isinstance(observation.get("metadata"), dict)
        ):
            metadata = observation["metadata"]
            segments.append({
                "start": observation.get("timestamp_start"),
                "end": observation.get("timestamp_end"),
                "text": metadata.get("text", ""),
            })
    if not segments:
        return jsonify({
            "status": "unavailable",
            "events": [],
            "warning": "No timestamped transcript segments were found for this evidence.",
        }), 404

    # This network call happens only after the user explicitly chooses event
    # extraction in the UI and confirms that transcript text may be sent.
    return jsonify(intelligence_service.extract_audio_events(segments, evidence_id))
