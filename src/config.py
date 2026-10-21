"""
config.py
─────────
Central application configuration for CrimeVision AI.

All tuneable values are read from environment variables (via .env).
Defaults are conservative so the app runs even without a .env file.
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# ── Project root ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# Load only the application-local environment file, never a parent directory's .env.
load_dotenv(BASE_DIR / ".env")


# ── Flask ─────────────────────────────────────────────────────────────────────
class FlaskConfig:
    # Generate a per-process key when none is configured. This keeps a fresh
    # local install usable without falling back to a publicly known secret.
    _insecure_secret_values = {
        "change-this-to-a-long-random-secret-key",
        "dev-insecure-key-change-in-production",
    }
    _configured_secret = os.getenv("SECRET_KEY", "").strip()
    SECRET_KEY: str = (
        _configured_secret
        if len(_configured_secret) >= 32 and _configured_secret not in _insecure_secret_values
        else secrets.token_urlsafe(32)
    )
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT: int = int(os.getenv("PORT", "5000"))
    _configured_cors_origins = os.getenv("CORS_ORIGINS", "").strip()
    CORS_ORIGINS: list[str] = (
        [origin.strip() for origin in _configured_cors_origins.split(",") if origin.strip()]
        if _configured_cors_origins
        else [f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"]
    )

    # Upload
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200")) * 1024 * 1024
    UPLOAD_FOLDER: Path = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    REPORTS_FOLDER: Path = BASE_DIR / os.getenv("REPORTS_FOLDER", "reports")
    DATA_FOLDER: Path = BASE_DIR / os.getenv("DATA_FOLDER", "data")

    # Allowed extensions
    ALLOWED_IMAGE_EXT: set = set(
        os.getenv("ALLOWED_IMAGE_EXTENSIONS", "jpg,jpeg,png,bmp,tiff,webp").split(",")
    )
    ALLOWED_AUDIO_EXT: set = set(
        os.getenv("ALLOWED_AUDIO_EXTENSIONS", "mp3,wav,m4a,ogg,flac,aac").split(",")
    )
    ALLOWED_VIDEO_EXT: set = set(
        os.getenv("ALLOWED_VIDEO_EXTENSIONS", "mp4,avi,mov,mkv,webm").split(",")
    )


# ── Groq LLM ──────────────────────────────────────────────────────────────────
class GroqConfig:
    API_KEY: str | None = os.getenv("GROQ_API_KEY")
    MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    IS_CONFIGURED: bool = bool(API_KEY and API_KEY != "your_groq_api_key_here")


# ── AI Model Settings ─────────────────────────────────────────────────────────
class ModelConfig:
    # Never fetch neural weights automatically. Set ALLOW_MODEL_DOWNLOADS=1
    # only after the user has explicitly approved downloading them.
    ALLOW_MODEL_DOWNLOADS: bool = os.getenv("ALLOW_MODEL_DOWNLOADS", "0") == "1"

    # RT-DETR
    RTDETR_MODEL: str = os.getenv("RTDETR_MODEL", "PekingU/rtdetr_r18vd")

    # Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")

    # BLIP
    BLIP_MODEL: str = os.getenv("BLIP_MODEL", "Salesforce/blip-image-captioning-base")

    # Feature flags
    ENABLE_BLIP: bool = os.getenv("ENABLE_BLIP", "1") == "1"
    ENABLE_CLIP: bool = os.getenv("ENABLE_CLIP", "1") == "1"
    ENABLE_SPEAKER_DIARIZATION: bool = os.getenv("ENABLE_SPEAKER_DIARIZATION", "0") == "1"


# ── Video Processing ──────────────────────────────────────────────────────────
class VideoConfig:
    FRAME_INTERVAL_SEC: float = float(os.getenv("VIDEO_FRAME_INTERVAL_SEC", "2"))
    MAX_FRAMES: int = int(os.getenv("VIDEO_MAX_FRAMES", "60"))
    # Reject extreme dimensions before asking OpenCV to decode a frame.
    MAX_FRAME_PIXELS: int = int(os.getenv("VIDEO_MAX_FRAME_PIXELS", "40000000"))


# ── Convenience aggregate ─────────────────────────────────────────────────────
class Config(FlaskConfig):
    """Single config object imported by app.py and services."""
    groq = GroqConfig
    models = ModelConfig
    video = VideoConfig

    @classmethod
    def ensure_directories(cls) -> None:
        """Create required runtime directories if they do not exist."""
        for folder in (cls.UPLOAD_FOLDER, cls.REPORTS_FOLDER, cls.DATA_FOLDER):
            folder.mkdir(parents=True, exist_ok=True)

    @classmethod
    def summary(cls) -> dict:
        """Return a non-sensitive configuration summary for the health endpoint."""
        return {
            "whisper_model": cls.models.WHISPER_MODEL,
            "rtdetr_model": cls.models.RTDETR_MODEL,
            "blip_model": cls.models.BLIP_MODEL,
            "groq_configured": cls.groq.IS_CONFIGURED,
            "groq_model": cls.groq.MODEL,
            "enable_blip": cls.models.ENABLE_BLIP,
            "enable_clip": cls.models.ENABLE_CLIP,
            "enable_speaker_diarization": cls.models.ENABLE_SPEAKER_DIARIZATION,
            "video_frame_interval_sec": cls.video.FRAME_INTERVAL_SEC,
            "video_max_frames": cls.video.MAX_FRAMES,
            "video_max_frame_pixels": cls.video.MAX_FRAME_PIXELS,
            "max_upload_mb": int(os.getenv("MAX_UPLOAD_SIZE_MB", "200")),
        }
