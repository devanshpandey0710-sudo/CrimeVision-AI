"""
app.py
──────
CrimeVision AI – Flask application entry point.

Registers all blueprints, configures logging, and ensures runtime
directories exist before the server starts.

Usage (Windows PowerShell):
    python app.py

Or with Flask CLI:
    $env:FLASK_APP = "app.py"
    flask run
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config

# ── Logging configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("crimevision")


def create_app() -> Flask:
    """Application factory."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # ── Flask configuration ───────────────────────────────────────────────────
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["UPLOAD_FOLDER"] = str(Config.UPLOAD_FOLDER)

    # Allow the local browser UI origins only. Additional trusted origins can
    # be configured explicitly with CORS_ORIGINS.
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    # ── Ensure runtime directories exist ─────────────────────────────────────
    Config.ensure_directories()

    # ── Register blueprints ───────────────────────────────────────────────────
    from routes.dashboard_routes import dashboard_bp
    from routes.image_routes import image_bp
    from routes.audio_routes import audio_bp
    from routes.video_routes import video_bp
    from routes.evidence_routes import evidence_bp
    from routes.chat_routes import chat_bp
    from routes.report_routes import report_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(report_bp)

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(413)
    def too_large(e):
        max_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
        return jsonify({"error": f"File too large. Maximum upload size is {max_mb} MB."}), 413

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(e):
        logger.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error. Check server logs."}), 500

    logger.info("CrimeVision AI application created successfully.")
    logger.info("Groq LLM: %s", "CONFIGURED" if Config.groq.IS_CONFIGURED else "NOT CONFIGURED")
    return app


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    application = create_app()
    port = Config.PORT
    debug = Config.DEBUG
    logger.info("Starting CrimeVision AI on http://127.0.0.1:%d  (debug=%s)", port, debug)
    application.run(host="127.0.0.1", port=port, debug=debug)
