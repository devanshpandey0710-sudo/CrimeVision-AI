"""
routes/chat_routes.py
─────────────────────
Evidence-grounded AI chat endpoints.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from services.chat_service import chat_service
from utils.case_paths import normalize_case_id

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.route("/ask", methods=["POST"])
def ask():
    """
    Answer an investigator's question grounded in stored evidence.

    JSON body:
      { "case_id": "...", "question": "..." }
    """
    body = request.get_json(silent=True) or {}
    case_id = normalize_case_id(body.get("case_id"))
    question = body.get("question", "").strip()

    if not case_id:
        return jsonify({"error": "A valid case_id is required."}), 400
    if not question:
        return jsonify({"error": "question is required."}), 400

    allow_external = body.get("allow_external") is True
    result = chat_service.ask(case_id, question, allow_external=allow_external)
    return jsonify(result)


@chat_bp.route("/history/<case_id>")
def get_history(case_id: str):
    """Return the conversation history for a case."""
    case_id = normalize_case_id(case_id)
    if not case_id:
        return jsonify({"error": "Invalid case_id."}), 400
    history = chat_service.get_history(case_id)
    return jsonify({"case_id": case_id, "history": history})


@chat_bp.route("/history/<case_id>", methods=["DELETE"])
def clear_history(case_id: str):
    """Clear the conversation history for a case."""
    case_id = normalize_case_id(case_id)
    if not case_id:
        return jsonify({"error": "Invalid case_id."}), 400
    chat_service.clear_history(case_id)
    return jsonify({"message": f"History cleared for case {case_id}."})
