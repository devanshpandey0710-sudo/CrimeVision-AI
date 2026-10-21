"""
utils/evidence_schema.py
────────────────────────
Defines the canonical evidence observation schema used by all analysis
services and the fusion layer.

Every observation produced by image, audio, or video services should
conform to the EvidenceObservation TypedDict so the fusion service
can merge them reliably.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from typing import TypedDict


# ── Observation TypedDict ─────────────────────────────────────────────────────

class DetectedObject(TypedDict, total=False):
    label: str
    confidence: float
    bbox: list[float]          # [x1, y1, x2, y2] normalised 0–1


class EvidenceObservation(TypedDict, total=False):
    event_id: str              # UUID
    case_id: str               # session / case identifier
    source_evidence_id: str    # UUID of the uploaded file
    modality: str              # "image" | "audio" | "video"
    timestamp_start: Optional[float]   # seconds relative to media, or None
    timestamp_end: Optional[float]
    timestamp_basis: str        # media_relative | wall_clock | unknown
    event_type: str            # e.g. "object_detection", "speech_segment"
    description: str
    detected_objects: list[DetectedObject]
    source_reference: str      # e.g. "frame_0045" or "segment_3"
    confidence: float          # 0.0–1.0
    uncertainty: str           # free-text note
    metadata: dict[str, Any]
    created_at: str            # ISO-8601


# ── Factory helpers ───────────────────────────────────────────────────────────

def new_event_id() -> str:
    return str(uuid.uuid4())


def make_observation(
    *,
    case_id: str,
    source_evidence_id: str,
    modality: str,
    event_type: str,
    description: str,
    detected_objects: Optional[list[DetectedObject]] = None,
    timestamp_start: Optional[float] = None,
    timestamp_end: Optional[float] = None,
    timestamp_basis: Optional[str] = None,
    source_reference: str = "",
    confidence: float = 1.0,
    uncertainty: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> EvidenceObservation:
    """Return a fully populated EvidenceObservation dict."""
    basis = timestamp_basis or (
        "media_relative"
        if modality in {"audio", "video"} and (timestamp_start is not None or timestamp_end is not None)
        else "unknown"
    )
    return EvidenceObservation(
        event_id=new_event_id(),
        case_id=case_id,
        source_evidence_id=source_evidence_id,
        modality=modality,
        timestamp_start=timestamp_start,
        timestamp_end=timestamp_end,
        timestamp_basis=basis,
        event_type=event_type,
        description=description,
        detected_objects=detected_objects or [],
        source_reference=source_reference,
        confidence=confidence,
        uncertainty=uncertainty,
        metadata=metadata or {},
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def validate_observation(obs: dict) -> tuple[bool, list[str]]:
    """
    Validate that a dict has the minimum required fields.

    Returns (is_valid, list_of_error_messages).
    """
    required = {"case_id", "source_evidence_id", "modality", "event_type", "description"}
    missing = required - obs.keys()
    errors: list[str] = [f"Missing required field: {f}" for f in sorted(missing)]

    modality_values = {"image", "audio", "video", "fusion"}
    if "modality" in obs and obs["modality"] not in modality_values:
        errors.append(
            f"Invalid modality '{obs['modality']}'. "
            f"Expected one of {modality_values}."
        )

    if "confidence" in obs:
        c = obs["confidence"]
        if not isinstance(c, (int, float)) or not (0.0 <= float(c) <= 1.0):
            errors.append("confidence must be a float in [0.0, 1.0].")

    return len(errors) == 0, errors
