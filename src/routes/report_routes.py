"""
routes/report_routes.py
───────────────────────
PDF report generation and download endpoints.
Full implementation in Phase 7.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, send_file, request

from config import Config
from services.report_service import report_service
from utils.case_paths import case_file_path, normalize_case_id

logger = logging.getLogger(__name__)
report_bp = Blueprint("report", __name__, url_prefix="/api/report")


@report_bp.route("/generate", methods=["POST"])
def generate_report():
    """
    Generate a PDF report for a case.

    JSON body:
      { "case_id": "..." }
    """
    body = request.get_json(silent=True) or {}
    case_id = normalize_case_id(body.get("case_id"))
    if not case_id:
        return jsonify({"error": "A valid case_id is required."}), 400

    output_path = case_file_path(Config.REPORTS_FOLDER, case_id, "_report.pdf")
    result = report_service.generate(case_id, output_path)
    if result.get("status") != "ok":
        status_code = 409 if output_path.exists() else 500
        return jsonify(result), status_code
    return jsonify(result)


@report_bp.route("/download/<case_id>")
def download_report(case_id: str):
    """Download a previously generated PDF report."""
    case_id = normalize_case_id(case_id)
    if not case_id:
        return jsonify({"error": "Invalid case_id."}), 400
    path = case_file_path(Config.REPORTS_FOLDER, case_id, "_report.pdf")
    if not path.exists():
        return jsonify({"error": "Report not found. Generate it first."}), 404
    return send_file(str(path), as_attachment=True, download_name=f"crimevision_report_{case_id}.pdf")
