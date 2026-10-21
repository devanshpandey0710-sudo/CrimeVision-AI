"""
services/image_service.py
─────────────────────────
Image analysis service for CrimeVision AI (Phase 3).

Responsibilities:
  - Object detection & forensic analysis via RT-DETR / lightweight vision backbones
  - Scene description & captioning via BLIP
  - Semantic tag alignment & zero-shot forensic scoring via CLIP
  - Forensic image metadata extraction (dimensions, EXIF / timestamps, color statistics, sharpness)
  - Automatic persistence of standardized observations into the case timeline
  - Resilient graceful degradation (CPU-safe, robust error handling)
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from config import Config
from utils.evidence_schema import make_observation
from services.fusion_service import fusion_service

logger = logging.getLogger(__name__)


class ImageService:
    """
    Forensic image analysis service with lazy-loading AI pipelines and
    comprehensive fallback forensic analysis.
    """

    _instance: Optional["ImageService"] = None

    def __init__(self) -> None:
        self._rtdetr_processor = None
        self._rtdetr_model = None
        self._blip_processor = None
        self._blip_model = None
        self._clip_processor = None
        self._clip_model = None
        self._models_loaded: bool = False
        self._status: dict[str, bool] = {
            "rtdetr": False,
            "blip": False,
            "clip": False,
        }

    # ── Singleton ─────────────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "ImageService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Model loading ─────────────────────────────────────────────────────────

    def load_models(self) -> dict[str, bool]:
        """
        Attempt to load AI models (RT-DETR, BLIP, CLIP) on CPU.
        Failures are captured gracefully and logged.
        """
        if self._models_loaded:
            return self._status

        # 1. RT-DETR
        try:
            logger.info("Loading RT-DETR model: %s", Config.models.RTDETR_MODEL)
            from transformers import RTDetrForObjectDetection, RTDetrImageProcessor
            self._rtdetr_processor = RTDetrImageProcessor.from_pretrained(
                Config.models.RTDETR_MODEL,
                local_files_only=not Config.models.ALLOW_MODEL_DOWNLOADS,
            )
            self._rtdetr_model = RTDetrForObjectDetection.from_pretrained(
                Config.models.RTDETR_MODEL,
                local_files_only=not Config.models.ALLOW_MODEL_DOWNLOADS,
            )
            self._rtdetr_model.eval()
            self._status["rtdetr"] = True
            logger.info("RT-DETR loaded successfully.")
        except Exception as exc:
            logger.warning("Could not load RT-DETR model (%s): %s", Config.models.RTDETR_MODEL, exc)
            self._status["rtdetr"] = False

        # 2. BLIP
        if Config.models.ENABLE_BLIP:
            try:
                logger.info("Loading BLIP captioning model: %s", Config.models.BLIP_MODEL)
                from transformers import BlipForConditionalGeneration, BlipProcessor
                self._blip_processor = BlipProcessor.from_pretrained(
                    Config.models.BLIP_MODEL,
                    local_files_only=not Config.models.ALLOW_MODEL_DOWNLOADS,
                )
                self._blip_model = BlipForConditionalGeneration.from_pretrained(
                    Config.models.BLIP_MODEL,
                    local_files_only=not Config.models.ALLOW_MODEL_DOWNLOADS,
                )
                self._blip_model.eval()
                self._status["blip"] = True
                logger.info("BLIP loaded successfully.")
            except Exception as exc:
                logger.warning("Could not load BLIP model (%s): %s", Config.models.BLIP_MODEL, exc)
                self._status["blip"] = False

        # 3. CLIP
        if Config.models.ENABLE_CLIP:
            try:
                logger.info("Loading CLIP model: openai/clip-vit-base-patch32")
                from transformers import CLIPModel, CLIPProcessor
                self._clip_processor = CLIPProcessor.from_pretrained(
                    "openai/clip-vit-base-patch32",
                    local_files_only=not Config.models.ALLOW_MODEL_DOWNLOADS,
                )
                self._clip_model = CLIPModel.from_pretrained(
                    "openai/clip-vit-base-patch32",
                    local_files_only=not Config.models.ALLOW_MODEL_DOWNLOADS,
                )
                self._clip_model.eval()
                self._status["clip"] = True
                logger.info("CLIP loaded successfully.")
            except Exception as exc:
                logger.warning("Could not load CLIP model: %s", exc)
                self._status["clip"] = False

        self._models_loaded = any(self._status.values())
        return self._status

    def is_ready(self) -> bool:
        """Return True if at least one AI model is loaded and ready."""
        return self._models_loaded

    # ── Image Analysis Pipeline ───────────────────────────────────────────────

    def analyse(
        self,
        image_path: Path,
        case_id: str,
        evidence_id: str,
    ) -> dict[str, Any]:
        """
        Execute full forensic image analysis pipeline:
          1. Metadata and forensic image metrics (resolution, sharpness, blur, color profile)
          2. RT-DETR object detection
          3. BLIP scene description
          4. CLIP forensic context classification
          5. Canonical observation generation & automatic persistence to case timeline
        """
        image_path = Path(image_path)
        if not image_path.exists():
            return {
                "status": "error",
                "error": f"Image file not found: {image_path}",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }

        # 1. Decode the image and compute image forensics. Pillow decodes lazily,
        # so force pixel loading here to catch truncated/corrupt uploads.
        try:
            with Image.open(image_path) as opened_image:
                opened_image.load()
                pil_img = opened_image.convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            logger.info("Image could not be decoded: %s", type(exc).__name__)
            return {
                "status": "error",
                "error": "The uploaded file is not a valid, readable image.",
                "case_id": case_id,
                "evidence_id": evidence_id,
            }
        width, height = pil_img.size

        from utils.file_utils import file_sha256
        img_sha256 = file_sha256(image_path)
        forensic_meta = self._extract_forensic_metadata(image_path, pil_img)
        forensic_meta["sha256"] = img_sha256

        # 2. Run object detection (RT-DETR or heuristic fallback)
        pipeline_results, det_engine, det_tier = self._detect_objects(pil_img)
        # Contour regions are not semantic object detections. Keep them
        # available as heuristic regions, but do not count or store them as
        # RT-DETR objects.
        detections = pipeline_results if det_tier == "deep_learning" else []
        candidate_regions = pipeline_results if det_tier == "heuristic_fallback" else []
        annotated_image_url = None
        if detections:
            annotated_image_url = self._save_annotated_image(pil_img, detections, evidence_id)

        # 3. Generate caption (BLIP or heuristic description)
        caption, cap_engine, cap_tier = self._generate_caption(pil_img, detections)

        # 4. Run forensic classification / zero-shot tag scoring (CLIP or forensic labels)
        tags, clip_engine, clip_tier = self._classify_scene(pil_img, detections, caption)

        # 5. Create standardized observations with explicit provenance
        observations: list[dict[str, Any]] = []

        # (a) Scene observation
        scene_conf = 0.88 if cap_tier == "deep_learning" else 0.70
        scene_obs = make_observation(
            case_id=case_id,
            source_evidence_id=evidence_id,
            modality="image",
            event_type="scene_description",
            description=f"Visual Scene: {caption}",
            confidence=scene_conf,
            uncertainty=(
                "Machine-generated caption; it may be incomplete and is not a forensic conclusion."
                if cap_tier == "deep_learning"
                else "Heuristic description; no image-captioning model produced this text."
            ),
            metadata={
                "file_name": image_path.name,
                "sha256": img_sha256,
                "resolution": f"{width}x{height}",
                "detected_objects_count": len(detections),
                "heuristic_regions_count": len(candidate_regions),
                "forensic_quality": forensic_meta.get("quality_rating", "good"),
                "blur_score": forensic_meta.get("blur_score", 0.0),
                "tags": [t["label"] for t in tags[:5]],
                "inference_engine": cap_engine,
                "inference_tier": cap_tier,
                "classification_engine": clip_engine,
            },
        )
        observations.append(scene_obs)

        # (b) Object observations only when a semantic detector actually ran
        for det in detections[:8]:
            det_obs = make_observation(
                case_id=case_id,
                source_evidence_id=evidence_id,
                modality="image",
                event_type="object_detection",
                description=f"Detected {det['label']} (confidence: {det['confidence']:.2f}) [{det.get('inference_tier', det_tier)}]",
                confidence=float(det["confidence"]),
                uncertainty="Model detections are predictions and require human review.",
                detected_objects=[{
                    "label": det["label"],
                    "confidence": float(det["confidence"]),
                    "bbox": det["box"],
                }],
                metadata={
                    "label": det["label"],
                    "box": det["box"],
                    "area_percentage": round(det.get("area_pct", 0.0), 2),
                    "sha256": img_sha256,
                    "inference_engine": det.get("inference_engine", det_engine),
                    "inference_tier": det.get("inference_tier", det_tier),
                },
            )
            observations.append(det_obs)

        # 6. Persist to case timeline automatically
        try:
            fusion_service.save_observations(case_id, observations)
        except Exception as exc:
            logger.error("Failed to persist image observations to case %s: %s", case_id, exc)

        return {
            "status": "ok",
            "case_id": case_id,
            "evidence_id": evidence_id,
            "file": image_path.name,
            "file_size": image_path.stat().st_size,
            "sha256": img_sha256,
            "inference_source": det_tier,
            "inference_engine": det_engine,
            "resolution": {"width": width, "height": height},
            "object_count": len(detections),
            "forensics": forensic_meta,
            "caption": caption,
            "detections": detections,
            "annotated_image_url": annotated_image_url,
            "candidate_regions": candidate_regions,
            "candidate_regions_note": (
                "OpenCV contour regions are not identified objects."
                if candidate_regions else None
            ),
            "tags": tags,
            "candidate_scene_categories": tags,
            "category_note": "Category scores are suggestions, not verified object detections or conclusions about a person.",
            "scenario_hypotheses": {
                "status": "not_generated",
                "items": [],
                "reason": "No explicit hypothesis request was made; evidence is not sent to an external model automatically.",
            },
            "observations_created": len(observations),
            "provenance": {
                "detection_engine": det_engine,
                "detection_tier": det_tier,
                "caption_engine": cap_engine,
                "caption_tier": cap_tier,
                "classification_engine": clip_engine,
                "classification_tier": clip_tier,
            },
            "models_used": {
                "rtdetr": det_tier == "deep_learning",
                "blip": cap_tier == "deep_learning",
                "clip": clip_tier == "deep_learning",
            },
        }

    @staticmethod
    def _save_annotated_image(image: Image.Image, detections: list[dict[str, Any]], evidence_id: str) -> str | None:
        """Save an annotated copy only for real model detections, never overwrite."""
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", evidence_id):
            return None
        output_path = Config.UPLOAD_FOLDER / f"annotated_{evidence_id}.jpg"
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        for detection in detections:
            x1, y1, x2, y2 = [int(round(value)) for value in detection.get("box", [0, 0, 0, 0])]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (40, 220, 120), 2)
            label = f"{detection.get('label', 'object')} {detection.get('confidence', 0):.2f}"
            cv2.putText(frame, label, (x1, max(16, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 220, 120), 1)
        encoded_ok, encoded = cv2.imencode(".jpg", frame)
        if not encoded_ok:
            return None
        try:
            Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
            with output_path.open("xb") as image_file:
                image_file.write(encoded.tobytes())
        except OSError as exc:
            logger.warning("Could not save annotated image: %s", type(exc).__name__)
            return None
        return f"/api/image/annotated/{evidence_id}"

    # ── Internal Analysis Methods ─────────────────────────────────────────────

    def _extract_forensic_metadata(self, path: Path, img: Image.Image) -> dict[str, Any]:
        """Compute basic forensic image metrics (blur detection, color channel stats, EXIF)."""
        np_img = np.array(img)
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)

        # Laplacian variance as a blur/sharpness metric
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < 100.0

        # Mean intensity and contrast
        mean_intensity = float(np.mean(gray))
        contrast = float(np.std(gray))

        # Color stats
        r_mean = float(np.mean(np_img[:, :, 0]))
        g_mean = float(np.mean(np_img[:, :, 1]))
        b_mean = float(np.mean(np_img[:, :, 2]))

        # EXIF datetime if available
        created_time = None
        exif = img.getexif()
        if exif:
            # 306 = DateTime, 36867 = DateTimeOriginal
            created_time = exif.get(36867) or exif.get(306)

        return {
            "sharpness_score": round(laplacian_var, 2),
            "blur_score": round(laplacian_var, 2),
            "is_blurry": is_blurry,
            "mean_luminance": round(mean_intensity, 2),
            "contrast": round(contrast, 2),
            "color_balance": {
                "red": round(r_mean, 1),
                "green": round(g_mean, 1),
                "blue": round(b_mean, 1),
            },
            "exif_timestamp": created_time,
            "quality_rating": "low_resolution" if (img.width < 320 or img.height < 240) else ("blurry" if is_blurry else "good"),
        }

    def _detect_objects(self, img: Image.Image) -> tuple[list[dict[str, Any]], str, str]:
        """Run RT-DETR object detection or fallback forensic CV."""
        if self._rtdetr_model is not None and self._rtdetr_processor is not None:
            try:
                import torch
                inputs = self._rtdetr_processor(images=img, return_tensors="pt")
                with torch.no_grad():
                    outputs = self._rtdetr_model(**inputs)

                target_sizes = torch.tensor([img.size[::-1]])
                results = self._rtdetr_processor.post_process_object_detection(
                    outputs, target_sizes=target_sizes, threshold=0.35
                )[0]

                detections = []
                w, h = img.size
                total_area = float(w * h)

                for score, label, box in zip(
                    results["scores"], results["labels"], results["boxes"]
                ):
                    b = [round(float(x), 1) for x in box.tolist()]
                    box_area = max(0.0, (b[2] - b[0]) * (b[3] - b[1]))
                    detections.append({
                        "label": self._rtdetr_model.config.id2label.get(int(label), f"object_{label}"),
                        "confidence": round(float(score), 3),
                        "box": b,
                        "area_pct": (box_area / total_area) * 100 if total_area > 0 else 0.0,
                        "inference_engine": "RT-DETR (PekingU/rtdetr_r18vd)",
                        "inference_tier": "deep_learning",
                    })
                return sorted(detections, key=lambda x: x["confidence"], reverse=True), "RT-DETR", "deep_learning"
            except Exception as exc:
                logger.warning("RT-DETR inference failed: %s, falling back to CV detection.", exc)

        # Fallback CV detector: detect contours / salient foreground objects
        fallback_dets = self._fallback_cv_detection(img)
        for d in fallback_dets:
            d["inference_engine"] = "OpenCV-ContourSaliency"
            d["inference_tier"] = "heuristic_fallback"
        return fallback_dets, "OpenCV-ContourSaliency", "heuristic_fallback"

    def _fallback_cv_detection(self, img: Image.Image) -> list[dict[str, Any]]:
        """Lightweight OpenCV contour and region detector for forensic analysis."""
        np_img = np.array(img)
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        w, h = img.size
        img_area = float(w * h)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (img_area * 0.02):  # significant foreground element
                x, y, bw, bh = cv2.boundingRect(cnt)
                area_pct = (float(bw * bh) / img_area) * 100.0
                detections.append({
                    "label": "salient_foreground_entity",
                    "confidence": 0.72,
                    "box": [float(x), float(y), float(x + bw), float(y + bh)],
                    "area_pct": round(area_pct, 2),
                })

        if not detections:
            detections.append({
                "label": "general_scene_surface",
                "confidence": 0.65,
                "box": [0.0, 0.0, float(w), float(h)],
                "area_pct": 100.0,
            })

        return detections[:10]

    def _generate_caption(self, img: Image.Image, detections: list[dict[str, Any]]) -> tuple[str, str, str]:
        """Run BLIP captioning or synthesize forensic scene descriptor."""
        if self._blip_model is not None and self._blip_processor is not None:
            try:
                import torch
                inputs = self._blip_processor(img, return_tensors="pt")
                with torch.no_grad():
                    out = self._blip_model.generate(**inputs, max_new_tokens=40)
                caption = self._blip_processor.decode(out[0], skip_special_tokens=True).strip()
                if caption:
                    return caption, "Salesforce/blip-image-captioning-base", "deep_learning"
            except Exception as exc:
                logger.warning("BLIP caption generation failed: %s", exc)

        # Synthesize forensic descriptor based on detected labels and image properties
        labels = [d["label"] for d in detections if d["label"] != "general_scene_surface"]
        if labels:
            unique_labels = list(dict.fromkeys(labels))
            return f"Forensic photograph showing {', '.join(unique_labels[:4])} at the scene.", "Heuristic-RuleBased", "heuristic_fallback"
        return f"Forensic evidentiary image capture ({img.width}x{img.height}) with visible environmental details.", "Heuristic-RuleBased", "heuristic_fallback"

    def _classify_scene(
        self, img: Image.Image, detections: list[dict[str, Any]], caption: str
    ) -> tuple[list[dict[str, Any]], str, str]:
        """Run CLIP zero-shot classification against forensic categories or rule-based matching."""
        categories = [
            "crime scene interior",
            "outdoor crime scene",
            "vehicle or transport",
            "weapon or dangerous instrument",
            "person or subject",
            "document or paper evidence",
            "digital electronic device",
            "bloodstain or biological trace",
            "residential room",
            "street or roadway",
        ]

        if self._clip_model is not None and self._clip_processor is not None:
            try:
                import torch
                inputs = self._clip_processor(
                    text=categories, images=img, return_tensors="pt", padding=True
                )
                with torch.no_grad():
                    outputs = self._clip_model(**inputs)
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1)[0].tolist()

                scored = [
                    {"label": cat, "score": round(float(p), 3)}
                    for cat, p in zip(categories, probs)
                ]
                return sorted(scored, key=lambda x: x["score"], reverse=True)[:5], "openai/clip-vit-base-patch32", "deep_learning"
            except Exception as exc:
                logger.warning("CLIP classification failed: %s", exc)

        # Rule-based fallback tags
        scored = []
        text_context = (caption + " " + " ".join(d["label"] for d in detections)).lower()
        for cat in categories:
            match_score = 0.40
            for word in cat.split():
                if word in text_context:
                    match_score += 0.25
            scored.append({"label": cat, "score": min(0.95, round(match_score, 2))})

        return sorted(scored, key=lambda x: x["score"], reverse=True)[:5], "Heuristic-RuleBased", "heuristic_fallback"


# Module-level singleton accessor
image_service = ImageService.get_instance()
