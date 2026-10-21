"""
routes/video_routes.py
──────────────────────
Video upload and analysis endpoints.
Full implementation in Phase 5.
"""

from __future__ import annotations

import logging
import re
import uuid

from flask import Blueprint, jsonify, request, send_file

from config import Config
from utils.file_utils import allowed_video, safe_save, sniff_magic
from services.video_service import video_service
from services.fusion_service import fusion_service
from services.intelligence_service import intelligence_service
from utils.case_paths import normalize_case_id

logger = logging.getLogger(__name__)
video_bp = Blueprint("video", __name__, url_prefix="/api/video")


@video_bp.route("/keyframes/<evidence_id>/<filename>", methods=["GET"])
def get_keyframe(evidence_id: str, filename: str):
    """Serve generated keyframes only for a UUID evidence ID and known filename shape."""
    try:
        safe_id = str(uuid.UUID(evidence_id))
    except (ValueError, AttributeError, TypeError):
        return jsonify({"error": "Invalid evidence identifier."}), 400
    if not re.fullmatch(r"frame_[0-9]{4}_[0-9]+s\.jpg", filename):
        return jsonify({"error": "Invalid keyframe filename."}), 400
    root = Config.UPLOAD_FOLDER.resolve()
    folder = (root / f"frames_{safe_id}").resolve()
    path = (folder / filename).resolve()
    if folder.parent != root or path.parent != folder:
        return jsonify({"error": "Invalid keyframe path."}), 400
    if not path.is_file():
        return jsonify({"error": "Keyframe is unavailable."}), 404
    return send_file(path, mimetype="image/jpeg", conditional=True)


@video_bp.route("/analyse", methods=["POST"])
def analyse_video():
    """
    Upload and analyse a video file.

    Form fields:
      file     – video file (required)
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

    if not allowed_video(file.filename):
        return jsonify({
            "error": f"Unsupported video format. "
                     f"Allowed: {', '.join(sorted(Config.ALLOWED_VIDEO_EXT))}."
        }), 415

    try:
        evidence_id, saved_path = safe_save(file, Config.UPLOAD_FOLDER)
    except (ValueError, OSError) as exc:
        logger.error("Video save failed: %s", exc)
        return jsonify({"error": f"Could not save file: {exc}"}), 500

    ext = saved_path.suffix.lstrip(".").lower()
    if not sniff_magic(saved_path, ext):
        saved_path.unlink(missing_ok=True)
        return jsonify({"error": "File content does not match its video extension."}), 415

    result = video_service.analyse(saved_path, case_id, evidence_id)
    if result.get("status") == "error":
        return jsonify(result), 422
    return jsonify(result)


@video_bp.route("/classify", methods=["POST"])
def classify_video_events():
    """Explicitly request tentative Groq classification of stored observations."""
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
            "classifications": [],
            "warning": "Set allow_external=true only after confirming that observation text may be sent.",
        }), 400
    if not intelligence_service.is_available:
        return jsonify({
            "status": "unavailable",
            "classifications": [],
            "warning": "Groq is not configured. No video observations were sent.",
        }), 503

    source_events = [
        observation
        for observation in fusion_service.load_observations(case_id)
        if observation.get("source_evidence_id") == evidence_id
        and observation.get("modality") == "video"
        and observation.get("event_type") in {"video_motion_change", "video_keyframe_detection"}
    ]
    if not source_events:
        return jsonify({
            "status": "unavailable",
            "classifications": [],
            "warning": "No analyzed observations were found for this video evidence.",
        }), 404

    # Only descriptions and source references leave the app, and only after an
    # explicit dashboard action and user confirmation.
    return jsonify(intelligence_service.classify_video_events(source_events, evidence_id))
