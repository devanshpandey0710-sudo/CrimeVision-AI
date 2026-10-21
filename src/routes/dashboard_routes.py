"""
routes/dashboard_routes.py
──────────────────────────
Dashboard and health-check endpoints.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template

from config import Config
from services.fusion_service import fusion_service

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")


@dashboard_bp.route("/api/health")
def health():
    """
    Health-check endpoint.

    Returns application status and a non-sensitive configuration summary.
    """
    return jsonify({
        "status": "ok",
        "application": "CrimeVision AI",
        "version": "1.0.0-phase1",
        "config": Config.summary(),
        "cases_on_disk": len(fusion_service.list_cases()),
    })


@dashboard_bp.route("/api/cases")
def list_cases():
    """Return the list of case IDs that have stored evidence."""
    cases = fusion_service.list_cases()
    return jsonify({"cases": cases, "count": len(cases)})


@dashboard_bp.route("/api/models/status")
def models_status():
    """
    Return the current load state of each AI model.

    Models are lazy-loaded on first use; this endpoint reports the last-known
    status without triggering model loading.
    """
    from services.image_service import image_service
    from services.audio_service import audio_service
    from services.intelligence_service import intelligence_service

    image_status = image_service._status if image_service._models_loaded else {
        "rtdetr": False, "blip": False, "clip": False,
    }

    return jsonify({
        "image_models": {
            "rtdetr": image_status.get("rtdetr", False),
            "blip": image_status.get("blip", False),
            "clip": image_status.get("clip", False),
            "any_loaded": image_service.is_ready(),
        },
        "audio_models": {
            "whisper": audio_service._status.get("whisper", False),
        },
        "llm": {
            "groq_configured": Config.groq.IS_CONFIGURED,
            "groq_available": intelligence_service.is_available,
            "groq_model": Config.groq.MODEL,
        },
        "inference_note": (
            "Models are lazy-loaded on first upload. "
            "Heuristic fallback is used until a model is confirmed loaded."
        ),
    })
