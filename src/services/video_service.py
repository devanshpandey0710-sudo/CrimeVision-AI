"""
services/video_service.py
─────────────────────────
Video analysis and keyframe extraction service for CrimeVision AI (Phase 5).

Capabilities:
  - Video stream decoding & forensic metadata extraction (duration, FPS, resolution, total frames)
  - Keyframe sampling at regular configurable time intervals (default: 2 sec)
  - Scene-change and motion detection based on frame differencing
  - Per-frame visual analysis using ImageService detection pipeline
  - Chronological timestamped event generation & automatic persistence into the case timeline
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image

from config import Config
from utils.evidence_schema import make_observation
from utils.timestamp_utils import seconds_to_hms
from services.fusion_service import fusion_service
from services.image_service import image_service

logger = logging.getLogger(__name__)


class VideoService:
    """
    Forensic video analysis service with keyframe extraction, scene change detection,
    and visual object detection.
    """

    _instance: Optional["VideoService"] = None

    def __init__(self) -> None:
        self._detector = None
        self._ready: bool = True

    @classmethod
    def get_instance(cls) -> "VideoService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_models(self) -> dict[str, bool]:
        """Ensures underlying video processing components are ready."""
        self._ready = True
        return {"video_extractor": True, "detector": True}

    def is_ready(self) -> bool:
        return self._ready

    def analyse(
        self,
        video_path: Path,
        case_id: str,
        evidence_id: str,
    ) -> dict[str, Any]:
        """
        Process a forensic video file:
          1. Read container metadata (FPS, frames, duration, resolution)
          2. Sample keyframes at VIDEO_FRAME_INTERVAL_SEC
          3. Compute frame-to-frame motion / scene change metric
          4. Run visual detection on representative keyframes
          5. Save timestamped observations into the case timeline
        """
        video_path = Path(video_path)
        if not video_path.exists():
            return {
                "status": "error",
                "error": f"Video file not found: {video_path}",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }

        from utils.file_utils import file_sha256
        video_sha256 = file_sha256(video_path)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {
                "status": "error",
                "error": f"Could not decode video file: {video_path.name}",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if fps <= 0 or total_frames <= 0 or width <= 0 or height <= 0:
            cap.release()
            return {
                "status": "error",
                "error": "Video metadata is incomplete or invalid; no frames were analyzed.",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }
        if width * height > Config.video.MAX_FRAME_PIXELS:
            cap.release()
            return {
                "status": "error",
                "error": "Video frame dimensions exceed the configured pixel limit.",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }
        duration = float(total_frames / fps)

        sample_interval_sec = max(0.1, float(Config.video.FRAME_INTERVAL_SEC or 2.0))
        frame_step = max(1, int(fps * sample_interval_sec))
        max_samples = min(max(1, int(Config.video.MAX_FRAMES or 60)), 300)

        keyframes = []
        observations: list[dict[str, Any]] = []
        prev_gray = None
        motion_events = []

        # Lightweight frame-to-frame entity tracking state
        # Tracks approximate spatial association across nearby sampled frames
        next_track_id = 1
        active_tracks: list[dict[str, Any]] = []  # [{"track_id": int, "box": list, "label": str, "last_seen_frame": int}]
        tracked_entities_summary: dict[int, dict[str, Any]] = {}

        # Track dominant inference tier across all sampled frames
        frame_tier_counts: dict[str, int] = {}

        frame_idx = 0
        sampled_count = 0

        # Create output directory for keyframes
        frame_dir = Config.UPLOAD_FOLDER / f"frames_{evidence_id}"
        frame_dir.mkdir(parents=True, exist_ok=True)

        while cap.isOpened() and sampled_count < max_samples:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            current_time_sec = round(float(frame_idx / fps), 2)
            # Work on a bounded-size copy and keep only sampled frames. This
            # reduces memory use while original video metadata remains reported.
            original_h, original_w = frame.shape[:2]
            scale = min(1.0, 1280 / max(original_w, original_h))
            if scale < 1.0:
                frame = cv2.resize(
                    frame,
                    (max(1, int(original_w * scale)), max(1, int(original_h * scale))),
                    interpolation=cv2.INTER_AREA,
                )
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Motion / Scene shift detection
            motion_score = 0.0
            if prev_gray is not None and prev_gray.shape == gray.shape:
                diff = cv2.absdiff(prev_gray, gray)
                motion_score = round(float(np.mean(diff)), 2)
                if motion_score > 30.0:  # significant visual shift or motion
                    motion_events.append({
                        "timestamp": current_time_sec,
                        "time_hms": seconds_to_hms(current_time_sec),
                        "motion_score": motion_score,
                        "frame_index": frame_idx,
                        "source_reference": f"frame_{sampled_count:04d}",
                    })
            prev_gray = gray

            # Save keyframe image
            keyframe_name = f"frame_{sampled_count:04d}_{int(current_time_sec)}s.jpg"
            keyframe_path = frame_dir / keyframe_name
            frame_saved = self._save_frame(frame, keyframe_path)
            if not frame_saved:
                cap.release()
                return {
                    "status": "error",
                    "error": "Could not save a sampled video frame; analysis stopped.",
                    "case_id": case_id,
                    "evidence_id": evidence_id,
                }

            # Analyze frame through visual pipeline
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(rgb_frame)
            frame_detections, det_engine, det_tier = image_service._detect_objects(pil_frame)
            frame_tier_counts[det_tier] = frame_tier_counts.get(det_tier, 0) + 1

            # OpenCV contour regions are candidate regions, not semantic object
            # detections. Only RT-DETR output is tracked or labeled as objects.
            candidate_regions = frame_detections if det_tier != "deep_learning" else []
            semantic_detections = frame_detections if det_tier == "deep_learning" else []
            if semantic_detections:
                for detection in semantic_detections:
                    x1, y1, x2, y2 = [int(round(value)) for value in detection.get("box", [0, 0, 0, 0])]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (40, 220, 120), 2)
                    label = f"{detection.get('label', 'object')} {detection.get('confidence', 0):.2f}"
                    cv2.putText(frame, label, (x1, max(16, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 220, 120), 1)
                if not self._save_frame(frame, keyframe_path):
                    cap.release()
                    return {
                        "status": "error",
                        "error": "Could not save the annotated keyframe.",
                        "case_id": case_id,
                        "evidence_id": evidence_id,
                    }

            # Lightweight frame-to-frame entity tracking association
            current_frame_tracked = []
            for det in semantic_detections:
                box = det.get("box", [0, 0, 0, 0])
                label = det.get("label", "entity")
                best_match = None
                best_iou = 0.20  # minimum spatial association threshold

                for trk in active_tracks:
                    iou = self._calculate_iou(box, trk["box"])
                    if iou > best_iou and (trk["label"] == label or trk["label"] == "entity"):
                        best_iou = iou
                        best_match = trk

                if best_match is not None:
                    tid = best_match["track_id"]
                    best_match["box"] = box
                    best_match["last_seen_frame"] = sampled_count
                    tracked_entities_summary[tid]["frames_count"] += 1
                    tracked_entities_summary[tid]["last_timestamp"] = current_time_sec
                else:
                    tid = next_track_id
                    next_track_id += 1
                    new_track = {
                        "track_id": tid,
                        "box": box,
                        "label": label,
                        "last_seen_frame": sampled_count,
                    }
                    active_tracks.append(new_track)
                    tracked_entities_summary[tid] = {
                        "track_id": tid,
                        "label": label,
                        "first_timestamp": current_time_sec,
                        "last_timestamp": current_time_sec,
                        "frames_count": 1,
                    }

                det["track_id"] = tid
                current_frame_tracked.append({
                    "track_id": tid,
                    "label": label,
                    "confidence": det.get("confidence", 0.70),
                    "box": box,
                })

            # Expire tracks not seen in last 2 sampled steps
            active_tracks = [t for t in active_tracks if (sampled_count - t["last_seen_frame"]) <= 2]

            keyframes.append({
                "frame_index": frame_idx,
                "timestamp": current_time_sec,
                "timestamp_hms": seconds_to_hms(current_time_sec),
                "motion_score": motion_score,
                "detections_count": len(semantic_detections),
                "candidate_regions_count": len(candidate_regions),
                "keyframe_file": keyframe_name,
                "detected_labels": [d["label"] for d in semantic_detections[:4]],
                "tracked_entities": current_frame_tracked[:5],
                "inference_engine": det_engine,
                "inference_tier": det_tier,
            })

            # Create timeline observation for frames with notable detections or motion
            if semantic_detections:
                labels_summary = ", ".join(f"{d['label']} (ID:{d.get('track_id')})" for d in semantic_detections[:3])
                # Build detected_objects list with track_id embedded in metadata field
                # so persisted observations carry genuine tracking information.
                obs_detected_objects = [
                    {
                        "label": d.get("label", "entity"),
                        "confidence": float(d.get("confidence", 0.70)),
                        "bbox": d.get("box", []),
                        "track_id": d.get("track_id"),
                    }
                    for d in semantic_detections[:8]
                ]
                obs = make_observation(
                    case_id=case_id,
                    source_evidence_id=evidence_id,
                    modality="video",
                    event_type="video_keyframe_detection",
                    description=f"Video @ {seconds_to_hms(current_time_sec)}: Detected {labels_summary} [{det_tier}]",
                    timestamp_start=current_time_sec,
                    timestamp_end=current_time_sec + sample_interval_sec,
                    source_reference=f"frame_{sampled_count:04d}",
                    confidence=float(semantic_detections[0].get("confidence", 0.75)),
                    detected_objects=obs_detected_objects,
                    metadata={
                        "frame_index": frame_idx,
                        "sha256": video_sha256,
                        "motion_score": motion_score,
                        "keyframe_file": keyframe_name,
                        "detections": semantic_detections[:5],
                        "candidate_regions": candidate_regions[:5],
                        "inference_engine": det_engine,
                        "inference_tier": det_tier,
                        "approximate_tracking_notice": "Entity IDs represent approximate spatial continuity, not biometric identity.",
                    },
                )
                observations.append(obs)

            sampled_count += 1
            frame_idx += frame_step
            if frame_idx >= total_frames:
                break

        cap.release()

        if not keyframes:
            return {
                "status": "error",
                "error": "No readable video frames were extracted; the video may be corrupt or unsupported by the installed codec.",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }

        # These are frame-difference observations only, not recognized actions.
        for motion in motion_events:
            observations.append(make_observation(
                case_id=case_id,
                source_evidence_id=evidence_id,
                modality="video",
                event_type="video_motion_change",
                description=(
                    f"Frame-difference motion change at {motion['time_hms']} "
                    f"(score {motion['motion_score']:.2f}); not an action classification."
                ),
                timestamp_start=motion["timestamp"],
                timestamp_end=motion["timestamp"],
                source_reference=motion["source_reference"],
                confidence=0.5,
                uncertainty="Heuristic frame difference; motion can reflect camera movement, lighting, or scene change.",
                metadata={
                    "motion_score": motion["motion_score"],
                    "frame_index": motion["frame_index"],
                    "sha256": video_sha256,
                    "inference_tier": "heuristic_fallback",
                },
            ))

        # Add overall video summary observation
        video_summary_obs = make_observation(
            case_id=case_id,
            source_evidence_id=evidence_id,
            modality="video",
            event_type="video_summary",
            description=(
                f"Video Footage ({width}x{height}, {duration:.1f}s, {fps:.1f} FPS): "
                f"{len(keyframes)} keyframes extracted, {len(tracked_entities_summary)} unique entity track(s) associated, "
                f"{len(motion_events)} motion spikes detected."
            ),
            timestamp_start=0.0,
            timestamp_end=duration,
            confidence=0.90,
            metadata={
                "file_name": video_path.name,
                "sha256": video_sha256,
                "resolution": f"{width}x{height}",
                "fps": round(fps, 2),
                "duration_seconds": round(duration, 2),
                "total_frames": total_frames,
                "sampled_keyframes": len(keyframes),
                "motion_events_count": len(motion_events),
                "tracked_entities_count": len(tracked_entities_summary),
            },
        )
        observations.insert(0, video_summary_obs)

        # Persist observations to case timeline
        try:
            fusion_service.save_observations(case_id, observations)
        except Exception as exc:
            logger.error("Failed to persist video observations to case %s: %s", case_id, exc)

        # Determine dominant inference tier across all sampled frames.
        # "deep_learning" wins if any frame used a real model; otherwise heuristic_fallback.
        if frame_tier_counts.get("deep_learning", 0) > 0:
            dominant_tier = "deep_learning"
            dominant_engine = "RT-DETR (PekingU/rtdetr_r18vd)"
        else:
            dominant_tier = "heuristic_fallback"
            dominant_engine = "OpenCV-ContourSaliency"

        return {
            "status": "ok",
            "case_id": case_id,
            "evidence_id": evidence_id,
            "file": video_path.name,
            "sha256": video_sha256,
            "inference_source": dominant_tier,
            "inference_engine": dominant_engine,
            "metadata": {
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "duration_seconds": round(duration, 2),
                "total_frames": total_frames,
            },
            "keyframes_extracted": len(keyframes),
            "keyframes": keyframes,
            "motion_events": motion_events,
            "tracked_entities": list(tracked_entities_summary.values()),
            "observations_created": len(observations),
            "tracking_disclaimer": "Lightweight spatial association across frames; not biometric identification.",
        }

    @staticmethod
    def _save_frame(frame: np.ndarray, path: Path) -> bool:
        """Encode JPEG bytes with OpenCV and write via pathlib for Unicode paths."""
        try:
            success, encoded = cv2.imencode(".jpg", frame)
            if not success:
                return False
            path.write_bytes(encoded.tobytes())
            return True
        except OSError as exc:
            logger.warning("Could not write keyframe %s: %s", path.name, exc)
            return False

    @staticmethod
    def _calculate_iou(boxA: list[float], boxB: list[float]) -> float:
        """Compute Intersection over Union between two bounding boxes [x1, y1, x2, y2]."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxAArea = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        boxBArea = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

        denom = boxAArea + boxBArea - interArea
        return (interArea / denom) if denom > 0 else 0.0


video_service = VideoService.get_instance()
