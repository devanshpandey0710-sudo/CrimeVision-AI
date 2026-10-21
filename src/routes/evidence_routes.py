"""
routes/evidence_routes.py
─────────────────────────
Evidence timeline and case management endpoints.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from services.fusion_service import fusion_service
from utils.case_paths import normalize_case_id

logger = logging.getLogger(__name__)
evidence_bp = Blueprint("evidence", __name__, url_prefix="/api/evidence")


@evidence_bp.route("/timeline/<case_id>")
def get_timeline(case_id: str):
    """Return the unified chronological timeline for a case."""
    case_id = normalize_case_id(case_id)
    if not case_id:
        return jsonify({"error": "Invalid case_id."}), 400
    timeline = fusion_service.get_timeline(case_id)
    return jsonify(timeline)


@evidence_bp.route("/cases")
def list_cases():
    """Return all case IDs with stored evidence."""
    cases = fusion_service.list_cases()
    return jsonify({"cases": cases, "count": len(cases)})


@evidence_bp.route("/case/<case_id>", methods=["DELETE"])
def delete_case(case_id: str):
    """Delete all stored evidence for a case."""
    case_id = normalize_case_id(case_id)
    if not case_id:
        return jsonify({"error": "Invalid case_id."}), 400
    deleted = fusion_service.delete_case(case_id)
    if deleted:
        return jsonify({"message": f"Case {case_id} deleted."})
    return jsonify({"error": f"Case {case_id} not found."}), 404
