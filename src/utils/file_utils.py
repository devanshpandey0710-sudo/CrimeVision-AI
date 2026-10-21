"""
utils/file_utils.py
───────────────────
Safe file-handling utilities for the CrimeVision AI upload pipeline.

Responsibilities:
  - Extension validation for image / audio / video uploads
  - Secure filename generation (UUID-based, no path traversal)
  - Saving uploaded files to the correct folder
  - Lightweight file-type sniffing via magic bytes
  - Cleanup helpers
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import Config

logger = logging.getLogger(__name__)

# ── Magic-byte signatures for basic format validation ─────────────────────────
_MAGIC: dict[str, list[bytes]] = {
    "jpg":  [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png":  [b"\x89PNG"],
    "gif":  [b"GIF87a", b"GIF89a"],
    "bmp":  [b"BM"],
    "webp": [b"RIFF"],
    "mp4":  [b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x1cftyp", b"ftyp"],
    "avi":  [b"RIFF"],
    "wav":  [b"RIFF"],
    "flac": [b"fLaC"],
    "ogg":  [b"OggS"],
    "mp3":  [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "m4a":  [b"ftyp"],
    "aac":  [b"\xff\xf1", b"\xff\xf9"],
}


def allowed_image(filename: str) -> bool:
    return _ext(filename) in Config.ALLOWED_IMAGE_EXT


def allowed_audio(filename: str) -> bool:
    return _ext(filename) in Config.ALLOWED_AUDIO_EXT


def allowed_video(filename: str) -> bool:
    return _ext(filename) in Config.ALLOWED_VIDEO_EXT


def _ext(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def generate_evidence_id() -> str:
    """Return a new UUID string to use as a unique evidence identifier."""
    return str(uuid.uuid4())


def safe_save(
    file: FileStorage,
    destination_folder: Path,
    evidence_id: Optional[str] = None,
) -> tuple[str, Path]:
    """
    Save a werkzeug FileStorage to *destination_folder* with a UUID-based name.

    Returns (evidence_id, absolute_path).
    Raises ValueError for empty filenames.
    Raises OSError for write failures.
    """
    if not file.filename:
        raise ValueError("Uploaded file has no filename.")

    original_name = secure_filename(file.filename)
    ext = _ext(original_name)
    eid = evidence_id or generate_evidence_id()
    dest_name = f"{eid}.{ext}"
    dest_path = destination_folder / dest_name

    destination_folder.mkdir(parents=True, exist_ok=True)
    file.save(str(dest_path))
    logger.info("Saved upload: %s -> %s", original_name, dest_path)
    return eid, dest_path


def sniff_magic(path: Path, declared_ext: str) -> bool:
    """
    Read the first 32 bytes of *path* and check against known magic bytes
    for *declared_ext*.  Returns True if recognised or if extension is
    not in our magic table (we give it the benefit of the doubt).
    """
    signatures = _MAGIC.get(declared_ext.lower())
    if not signatures:
        return True  # unknown extension – let the service handle it
    try:
        with open(path, "rb") as fh:
            header = fh.read(32)
        return any(header.startswith(sig) for sig in signatures)
    except OSError:
        return False


def file_sha256(path: Path) -> str:
    """
    Return the SHA-256 hex digest of a file for forensic verification and deduplication.
    Note: Cryptographic hashing identifies file content changes; it is not independent
    proof of legal chain of custody.
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_file_sha256(path: Path) -> str:
    """Alias for file_sha256."""
    return file_sha256(path)


def safe_delete(path: Path) -> bool:
    """Delete a file if it exists. Returns True on success."""
    try:
        if path.exists():
            path.unlink()
            logger.debug("Deleted: %s", path)
            return True
    except OSError as exc:
        logger.warning("Could not delete %s: %s", path, exc)
    return False


def cleanup_case_uploads(case_id: str) -> int:
    """
    Delete all upload files whose stem starts with *case_id*.
    Returns the number of files deleted.
    """
    deleted = 0
    for p in Config.UPLOAD_FOLDER.iterdir():
        if p.is_file() and p.stem.startswith(case_id):
            if safe_delete(p):
                deleted += 1
    return deleted


def human_size(n_bytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes //= 1024
    return f"{n_bytes:.1f} TB"
