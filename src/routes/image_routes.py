"""
routes/image_routes.py
──────────────────────
Image upload and analysis endpoints.
Full implementation in Phase 3.
"""

from __future__ import annotations

import logging
from pathlib import Path
import uuid

from flask import Blueprint, jsonify, request, send_file

from config import Config
from utils.file_utils import allowed_image, safe_save, sniff_magic, human_size
from services.image_service import image_service
from services.intelligence_service import intelligence_service
from services.fusion_service import fusion_service
from utils.case_paths import normalize_case_id

logger = logging.getLogger(__name__)
image_bp = Blueprint("image", __name__, url_prefix="/api/image")


@image_bp.route("/analyse", methods=["POST"])
def analyse_image():
    """
    Upload and analyse a single image.

    Form fields:
      file     – image file (required)
      case_id  – case / session identifier (required)
    """
    case_id = normalize_case_id(request.form.get("case_id"))
    if not case_id:
        return jsonify({"error": "A valid case_id is required."}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected."}), 400

    if not allowed_image(file.filename):
        return jsonify({
            "error": f"Unsupported image format. "
                     f"Allowed: {', '.join(sorted(Config.ALLOWED_IMAGE_EXT))}."
        }), 415

    try:
        evidence_id, saved_path = safe_save(file, Config.UPLOAD_FOLDER)
    except (ValueError, OSError) as exc:
        logger.error("Image save failed: %s", exc)
        return jsonify({"error": f"Could not save file: {exc}"}), 500

    ext = saved_path.suffix.lstrip(".").lower()
    if not sniff_magic(saved_path, ext):
        saved_path.unlink(missing_ok=True)
        return jsonify({"error": "File content does not match its extension."}), 415

    result = image_service.analyse(saved_path, case_id, evidence_id)
    if result.get("status") == "error":
        return jsonify(result), 422
    return jsonify(result)


@image_bp.route("/annotated/<evidence_id>", methods=["GET"])
def get_annotated_image(evidence_id: str):
    """Serve only a generated annotated image whose name contains a valid UUID."""
    try:
        safe_id = str(uuid.UUID(evidence_id))
    except (ValueError, AttributeError, TypeError):
        return jsonify({"error": "Invalid evidence identifier."}), 400
    path = (Config.UPLOAD_FOLDER / f"annotated_{safe_id}.jpg").resolve()
    root = Config.UPLOAD_FOLDER.resolve()
    if path.parent != root:
        return jsonify({"error": "Invalid evidence path."}), 400
    if not path.is_file():
        return jsonify({"error": "Annotated image is unavailable."}), 404
    return send_file(path, mimetype="image/jpeg", conditional=True)


@image_bp.route("/hypotheses", methods=["POST"])
def generate_image_hypotheses():
    """Optionally summarize stored image observations after explicit consent."""
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
            "summary": None,
            "hypotheses": [],
            "warning": "Set allow_external=true only after confirming that observation text may be sent.",
        }), 400
    if not intelligence_service.is_available:
        return jsonify({
            "status": "unavailable",
            "summary": None,
            "hypotheses": [],
            "warning": "Groq is not configured. No image observations were sent.",
        }), 503

    source_events = [
        observation
        for observation in fusion_service.load_observations(case_id)
        if observation.get("source_evidence_id") == evidence_id
        and observation.get("modality") == "image"
    ]
    if not source_events:
        return jsonify({
            "status": "unavailable",
            "summary": None,
            "hypotheses": [],
            "warning": "No analyzed image observations were found for this evidence.",
        }), 404
    # The service receives stored textual observations only, never the image path or pixels.
    return jsonify(intelligence_service.generate_image_hypotheses(source_events, evidence_id))
