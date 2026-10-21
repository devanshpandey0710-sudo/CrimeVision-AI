"""
services/fusion_service.py
──────────────────────────
Multimodal fusion & evidence timeline correlation service for CrimeVision AI (Phase 6).

Responsibilities:
  - Canonical JSON evidence store for cross-modal observations
  - Chronological sorting, normalization, and semantic de-duplication
  - Multi-source cross-referencing (matching visual objects with audio mentions)
  - Unified investigative timeline generation
  - Incident hypothesis generation and discrepancy tracking
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from config import Config
from utils.timestamp_utils import sort_key, seconds_to_hms
from utils.case_paths import case_file_path

logger = logging.getLogger(__name__)


class FusionService:
    _instance = None

    @classmethod
    def get_instance(cls) -> "FusionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Evidence storage helpers ──────────────────────────────────────────────

    def _case_file(self, case_id: str) -> Path:
        Config.DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        return case_file_path(Config.DATA_FOLDER, case_id, ".json")

    def save_observations(self, case_id: str, observations: list[dict]) -> None:
        """Append observations while dropping exact semantic duplicates only."""
        existing = self.load_observations(case_id)
        seen_ids = {o.get("event_id") for o in existing if "event_id" in o}
        def fingerprint(observation: dict) -> str:
            comparable = {
                key: value for key, value in observation.items()
                if key not in {"event_id", "created_at"}
            }
            return json.dumps(comparable, sort_keys=True, ensure_ascii=False, default=str)

        seen_content = {fingerprint(o) for o in existing}
        unique_new = []
        for observation in observations:
            content_id = fingerprint(observation)
            if observation.get("event_id") in seen_ids or content_id in seen_content:
                continue
            unique_new.append(observation)
            seen_ids.add(observation.get("event_id"))
            seen_content.add(content_id)
        merged = existing + unique_new
        self._case_file(case_id).write_text(
            json.dumps(merged, indent=2), encoding="utf-8"
        )
        logger.info(
            "Saved %d observations for case %s (total: %d).",
            len(unique_new), case_id, len(merged),
        )

    def load_observations(self, case_id: str) -> list[dict]:
        """Load all stored observations for a case. Returns [] if none."""
        path = self._case_file(case_id)
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read case file %s: %s", path, exc)
            return []

    def get_timeline(self, case_id: str) -> dict[str, Any]:
        """
        Return a sorted, fused chronological timeline with modality breakdown,
        cross-modal correlations, and forensic tags.
        """
        observations = self.load_observations(case_id)
        # Media-relative seconds are only comparable within the same evidence
        # file. Group by source first; then sort within each source.
        for observation in observations:
            if "timestamp_basis" not in observation:
                observation["timestamp_basis"] = (
                    "media_relative"
                    if observation.get("modality") in {"audio", "video"}
                    and observation.get("timestamp_start") is not None
                    else "unknown"
                )
        sorted_obs = sorted(
            observations,
            key=lambda o: (
                0 if o.get("timestamp_basis") == "wall_clock" else 1,
                str(o.get("source_evidence_id") or ""),
                sort_key(o.get("timestamp_start")),
                str(o.get("created_at") or ""),
            ),
        )

        # Modality aggregation
        modality_counts: dict[str, int] = defaultdict(int)
        entities_found: set[str] = set()

        for obs in sorted_obs:
            mod = obs.get("modality", "unknown")
            modality_counts[mod] += 1
            # Collect detected entities
            for det in obs.get("detected_objects", []):
                if isinstance(det, dict) and det.get("label"):
                    entities_found.add(det["label"])

        # Cross-modal correlation detection
        correlations = self._correlate_evidence(sorted_obs)

        return {
            "case_id": case_id,
            "total_observations": len(sorted_obs),
            "modality_breakdown": dict(modality_counts),
            "unique_entities_detected": sorted(list(entities_found)),
            "correlations": correlations,
            "time_axis_note": (
                "Media-relative timestamps are grouped by source evidence and are not synchronized across separate files. "
                "No real-world capture time is inferred."
            ),
            "observations": sorted_obs,
        }

    def _correlate_evidence(self, observations: list[dict]) -> list[dict[str, Any]]:
        """Identify overlapping visual and audio events occurring in close temporal proximity."""
        correlations = []
        image_or_video = [o for o in observations if o.get("modality") in ("image", "video")]
        audio_obs = [o for o in observations if o.get("modality") == "audio"]

        for v in image_or_video:
            v_start = v.get("timestamp_start")
            v_desc = (v.get("description") or "").lower()
            for a in audio_obs:
                a_start = a.get("timestamp_start")
                a_desc = (a.get("description") or "").lower()

                # Media-relative times are comparable only when both refer to
                # the exact same source file. Different files need clock-sync data.
                time_close = False
                same_source = (
                    v.get("source_evidence_id")
                    and v.get("source_evidence_id") == a.get("source_evidence_id")
                )
                same_basis = v.get("timestamp_basis") == a.get("timestamp_basis")
                if v_start is not None and a_start is not None and same_source and same_basis:
                    if abs(v_start - a_start) <= 5.0:
                        time_close = True

                # Semantic overlap
                common_terms = set(v_desc.split()).intersection(set(a_desc.split()))
                meaningful_common = {w for w in common_terms if len(w) > 4 and w not in ("detected", "visual", "speech")}

                if time_close or meaningful_common:
                    correlations.append({
                        "type": "temporal_match" if time_close else "semantic_match",
                        "visual_event_id": v.get("event_id"),
                        "audio_event_id": a.get("event_id"),
                        "visual_summary": v.get("description"),
                        "audio_summary": a.get("description"),
                        "common_cues": list(meaningful_common),
                    })

        return correlations[:10]

    def list_cases(self) -> list[str]:
        """Return a list of case IDs that have stored data."""
        return [p.stem for p in Config.DATA_FOLDER.glob("*.json")]

    def delete_case(self, case_id: str) -> bool:
        """Delete all stored data for a case. Returns True on success."""
        path = self._case_file(case_id)
        if path.exists():
            path.unlink()
            logger.info("Deleted case data: %s", case_id)
            return True
        return False


fusion_service = FusionService.get_instance()
