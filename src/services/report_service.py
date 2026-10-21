"""
services/report_service.py
──────────────────────────
Automated academic prototype report generator for CrimeVision AI (Activity 6.3).

Reports recorded observations and their limitations using ReportLab.
Generated files are not legally validated and do not establish chain of custody.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import Config
from services.fusion_service import fusion_service
from utils.timestamp_utils import seconds_to_hms

logger = logging.getLogger(__name__)


def _detected_labels(source_observations: list[dict[str, Any]]) -> Counter[str]:
    """Count only labels from well-formed semantic detection records."""
    labels: Counter[str] = Counter()
    for observation in source_observations:
        detected_objects = observation.get("detected_objects")
        if observation.get("event_type") != "object_detection" and observation.get("event_type") != "video_keyframe_detection":
            continue
        if not isinstance(detected_objects, list):
            continue
        for detected in detected_objects:
            if isinstance(detected, dict) and detected.get("label"):
                labels[str(detected["label"])] += 1
    return labels


class ReportService:
    _instance: Optional["ReportService"] = None

    @classmethod
    def get_instance(cls) -> "ReportService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate(
        self,
        case_id: str,
        output_path: Path,
        extra_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate a comprehensive PDF forensic report for the given case.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            return {
                "status": "error",
                "error": "A report already exists for this case. Download it or choose a new output path before generating another.",
            }

        timeline = fusion_service.get_timeline(case_id)
        observations = timeline.get("observations", [])
        breakdown = timeline.get("modality_breakdown", {})

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=landscape(letter),
            rightMargin=36,
            leftMargin=36,
            topMargin=28,
            bottomMargin=42,
        )

        def draw_footer(canvas, document):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#64748b"))
            canvas.drawString(36, 22, "Academic prototype - not legally validated; verify all source evidence.")
            canvas.drawRightString(document.pagesize[0] - 36, 22, f"Page {document.page}")
            canvas.restoreState()

        def safe_text(value: Any) -> str:
            return escape(str(value or ""))

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0284c7"),
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1e293b"),
        )
        table_cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#0f172a"),
        )
        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white,
        )

        elements = []

        # 1. Header
        elements.append(Paragraph("CRIMEVISION AI - ACADEMIC CASE ANALYSIS SUMMARY", title_style))
        elements.append(Paragraph("Machine-generated prototype report; not an official forensic finding", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=14))

        # 2. Case Metadata Table
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_data = [
            [
                Paragraph("<b>Case ID:</b>", body_style),
                Paragraph(safe_text(case_id), table_cell_bold),
                Paragraph("<b>Generated:</b>", body_style),
                Paragraph(now_str, body_style),
            ],
            [
                Paragraph("<b>Platform:</b>", body_style),
                Paragraph("CrimeVision AI v1.0", body_style),
                Paragraph("<b>Investigator:</b>", body_style),
                Paragraph("Forensics Division", body_style),
            ],
            [
                Paragraph("<b>Total Records:</b>", body_style),
                Paragraph(str(len(observations)), table_cell_bold),
                Paragraph("<b>Evidence Breakdown:</b>", body_style),
                Paragraph(
                    f"Images: {breakdown.get('image', 0)} | Audio: {breakdown.get('audio', 0)} | Video: {breakdown.get('video', 0)}",
                    body_style,
                ),
            ],
        ]

        meta_table = Table(meta_data, colWidths=[90, 170, 100, 170])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        # 3. Executive Summary
        elements.append(Paragraph("1. Executive Summary", h2_style))
        img_count = breakdown.get("image", 0)
        audio_count = breakdown.get("audio", 0)
        video_count = breakdown.get("video", 0)
        corrs = timeline.get("correlations", [])

        components = []
        if img_count > 0:
            components.append(f"visual forensic inspections across {img_count} image observation(s)")
        if audio_count > 0:
            components.append(f"acoustic analysis and, where available, speech transcription across {audio_count} audio observation(s)")
        if video_count > 0:
            components.append(f"video keyframe and frame-change processing across {video_count} video observation(s)")

        if components:
            comp_str = ", ".join(components)
            exec_summary_text = (
                f"Case <b>{safe_text(case_id)}</b> contains {len(observations)} recorded observation(s). "
                f"Completed analyses incorporate {comp_str}. "
            )
        else:
            exec_summary_text = f"Case <b>{safe_text(case_id)}</b> currently contains {len(observations)} recorded observation(s). "

        if corrs:
            exec_summary_text += f"Cross-evidence fusion identified {len(corrs)} multi-source temporal/semantic correlation(s)."
        else:
            exec_summary_text += "No cross-modal correlations were established for this evidence set."

        elements.append(Paragraph(exec_summary_text, body_style))
        elements.append(Spacer(1, 10))

        # Modality-specific summaries make the required image, audio, and
        # video outputs easy to find; the full observations remain in the timeline.
        elements.append(Paragraph("2. Modality Summaries", h2_style))
        modality_sections = [
            ("image", "Image Detection and Scene Summaries"),
            ("audio", "Audio Transcript Summaries"),
            ("video", "Video Event Summaries"),
        ]
        for modality, summary_title in modality_sections:
            elements.append(Paragraph(summary_title, subtitle_style))
            grouped_observations: dict[str, list[dict[str, Any]]] = {}
            for observation in observations:
                if observation.get("modality") == modality:
                    source_id = str(observation.get("source_evidence_id") or "not recorded")
                    grouped_observations.setdefault(source_id, []).append(observation)

            if not grouped_observations:
                elements.append(Paragraph(f"No {modality} observations are recorded.", body_style))
                continue

            summary_rows = [[
                Paragraph("Source Evidence ID", table_header_style),
                Paragraph("Recorded Summary", table_header_style),
            ]]
            for source_id, source_observations in grouped_observations.items():
                summary_parts: list[str] = []
                if modality == "image":
                    detection_observations = [
                        item for item in source_observations
                        if item.get("event_type") == "object_detection"
                    ]
                    labels = _detected_labels(detection_observations)
                    summary_parts.append(
                        f"{len(detection_observations)} recorded semantic object detection(s)."
                        if detection_observations else "No semantic object detections recorded."
                    )
                    if labels:
                        summary_parts.append("Labels: " + ", ".join(
                            f"{label} ({count})" for label, count in sorted(labels.items())
                        ) + ".")
                    scene_descriptions = [
                        str(item.get("description", ""))[:300]
                        for item in source_observations
                        if item.get("event_type") == "scene_description" and item.get("description")
                    ]
                    if scene_descriptions:
                        summary_parts.append("Scene description: " + scene_descriptions[0])
                elif modality == "audio":
                    speech_segments = [
                        item for item in source_observations
                        if item.get("event_type") == "speech_segment"
                    ]
                    excerpts = []
                    for item in speech_segments[:3]:
                        metadata = item.get("metadata")
                        metadata = metadata if isinstance(metadata, dict) else {}
                        excerpts.append(
                            str(metadata.get("text") or item.get("description", ""))[:180]
                        )
                    summary_parts.append(f"{len(speech_segments)} timestamped speech segment(s) recorded.")
                    if excerpts:
                        summary_parts.append("Transcript excerpts: " + " | ".join(excerpts))
                    elif not speech_segments:
                        audio_summaries = [
                            str(item.get("description", ""))[:300]
                            for item in source_observations
                            if item.get("event_type") == "audio_summary" and item.get("description")
                        ]
                        summary_parts.append(
                            audio_summaries[0] if audio_summaries
                            else "No transcript text is recorded; review the full timeline for acoustic observations."
                        )
                    if len(speech_segments) > len(excerpts):
                        summary_parts.append(
                            f"{len(speech_segments) - len(excerpts)} additional segment(s) appear in the full timeline."
                        )
                else:
                    frame_events = [
                        item for item in source_observations
                        if item.get("event_type") == "video_keyframe_detection"
                    ]
                    motion_events = [
                        item for item in source_observations
                        if item.get("event_type") == "video_motion_change"
                    ]
                    labels = _detected_labels(frame_events)
                    summary_parts.append(
                        f"{len(frame_events)} keyframe detection event(s); "
                        f"{len(motion_events)} heuristic frame-change event(s)."
                    )
                    if labels:
                        summary_parts.append("Detected labels: " + ", ".join(
                            f"{label} ({count})" for label, count in sorted(labels.items())
                        ) + ".")
                    if motion_events:
                        summary_parts.append("Frame changes are not action classifications.")

                summary_rows.append([
                    Paragraph(safe_text(source_id), table_cell_style),
                    Paragraph(safe_text(" ".join(summary_parts)), table_cell_style),
                ])

            summary_table = Table(summary_rows, colWidths=[150, 570], repeatRows=1)
            summary_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 6))

        # Evidence inventory, including sources without hashes or detections.
        elements.append(Paragraph("3. Evidence Inventory", h2_style))
        inventory: dict[str, dict[str, Any]] = {}
        for observation in observations:
            evidence_id = str(observation.get("source_evidence_id") or "")
            if not evidence_id:
                continue
            item = inventory.setdefault(evidence_id, {
                "file_name": "",
                "modalities": set(),
                "observation_count": 0,
            })
            item["file_name"] = item["file_name"] or (observation.get("metadata") or {}).get("file_name", "")
            item["modalities"].add(str(observation.get("modality") or "unknown"))
            item["observation_count"] += 1
        if inventory:
            inventory_rows = [[
                Paragraph("Source Evidence ID", table_header_style),
                Paragraph("File Name", table_header_style),
                Paragraph("Modality", table_header_style),
                Paragraph("Observation Count", table_header_style),
            ]]
            for evidence_id, item in inventory.items():
                inventory_rows.append([
                    Paragraph(safe_text(evidence_id), table_cell_style),
                    Paragraph(safe_text(item["file_name"] or "not recorded"), table_cell_style),
                    Paragraph(safe_text(", ".join(sorted(item["modalities"]))), table_cell_style),
                    Paragraph(str(item["observation_count"]), table_cell_style),
                ])
            inventory_table = Table(inventory_rows, colWidths=[190, 220, 140, 140], repeatRows=1)
            inventory_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            elements.append(inventory_table)
        else:
            elements.append(Paragraph("No source evidence identifiers are recorded.", body_style))
        elements.append(Spacer(1, 12))

        # 3. Evidence Timeline Table. Times are explicitly relative to source media.
        elements.append(Paragraph("4. Evidence Timeline", h2_style))

        if not observations:
            elements.append(Paragraph("<i>No forensic evidence observations recorded for this case.</i>", body_style))
        else:
            t_rows = [[
                Paragraph("Source ID", table_header_style),
                Paragraph("Timestamp & Basis", table_header_style),
                Paragraph("Modality", table_header_style),
                Paragraph("Event Type", table_header_style),
                Paragraph("Recorded Description", table_header_style),
                Paragraph("Conf.", table_header_style),
                Paragraph("Processing Engine / Tier", table_header_style),
                Paragraph("Analysis Time (UTC)", table_header_style),
            ]]

            for o in observations:
                ts = o.get("timestamp_start")
                basis = o.get("timestamp_basis", "unknown")
                ts_display = f"{seconds_to_hms(ts)} ({basis})" if ts is not None else "unknown"
                mod = (o.get("modality") or "?").upper()
                ev_type = (o.get("event_type") or "observation").replace("_", " ")
                desc = o.get("description", "")
                conf = f"{o.get('confidence', 0.0):.2f}"
                metadata = o.get("metadata") if isinstance(o.get("metadata"), dict) else {}
                engine = str(metadata.get("inference_engine") or "not recorded")[:100]
                tier = str(metadata.get("inference_tier") or "")[:40]
                processing = safe_text(engine)
                if tier:
                    processing += f"<br/><i>{safe_text(tier)}</i>"

                t_rows.append([
                    Paragraph(safe_text(o.get("source_evidence_id", "")), table_cell_style),
                    Paragraph(safe_text(ts_display), table_cell_style),
                    Paragraph(safe_text(mod), table_cell_style),
                    Paragraph(safe_text(ev_type), table_cell_style),
                    Paragraph(safe_text(desc), table_cell_style),
                    Paragraph(conf, table_cell_style),
                    Paragraph(processing, table_cell_style),
                    Paragraph(safe_text(o.get("created_at", "unknown")), table_cell_style),
                ])

            timeline_table = Table(t_rows, colWidths=[90, 90, 48, 60, 170, 35, 100, 127], repeatRows=1)
            timeline_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(timeline_table)

        elements.append(Spacer(1, 2))

        # 4. Evidence File Integrity (SHA-256)
        # Collect unique (evidence_id, filename, sha256) tuples from observation metadata.
        # Deduplicated by source_evidence_id so each uploaded file appears once.
        seen_evidence_ids: set[str] = set()
        hash_rows: list[tuple[str, str, str]] = []  # (evidence_id, filename, sha256)
        for o in observations:
            eid = o.get("source_evidence_id", "")
            if not eid or eid in seen_evidence_ids:
                continue
            seen_evidence_ids.add(eid)
            meta = o.get("metadata") or {}
            sha = meta.get("sha256") or ""
            if not sha:
                continue  # skip observations with no hash (legacy/stub records)
            fname = meta.get("file_name") or eid
            hash_rows.append((eid, fname, sha))

        elements.append(Paragraph("5. Evidence File Integrity (SHA-256)", h2_style))
        integrity_note = (
            "SHA-256 digests are recorded analysis metadata. They can be used to compare file bytes "
            "when independently recomputed; this report does not prove when a file changed, establish "
            "chain of custody, or establish legal admissibility."
        )
        elements.append(Paragraph(integrity_note, body_style))
        elements.append(Spacer(1, 3))

        if not hash_rows:
            elements.append(Paragraph("<i>No SHA-256 hash data available for this case.</i>", body_style))
        else:
            h_header = [
                Paragraph("Evidence ID", table_header_style),
                Paragraph("File Name", table_header_style),
                Paragraph("SHA-256 Digest", table_header_style),
            ]
            h_data = [h_header]
            hash_cell_style = ParagraphStyle(
                "HashCell",
                parent=table_cell_style,
                fontName="Courier",
                fontSize=7.0,
                leading=9.0,
                textColor=colors.HexColor("#0f172a"),
            )
            for eid, fname, sha in hash_rows:
                sha_display = sha if sha else "-"
                h_data.append([
                    Paragraph(safe_text(eid), table_cell_style),
                    Paragraph(safe_text(fname), table_cell_style),
                    Paragraph(
                        f"{sha_display[:32]}<br/>{sha_display[32:]}" if len(sha_display) > 32 else sha_display,
                        hash_cell_style,
                    ),
                ])
            hash_table = Table(h_data, colWidths=[110, 150, 272])
            hash_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(hash_table)

        elements.append(Spacer(1, 2))

        elements.append(Paragraph("6. Machine-Generated Interpretations", h2_style))
        interpretation_items = [
            observation for observation in observations
            if any(word in str(observation.get("event_type", "")).lower() for word in ("hypothesis", "interpretation", "classification"))
        ]
        if interpretation_items:
            for observation in interpretation_items[:20]:
                elements.append(Paragraph(
                    f"<b>{safe_text(observation.get('event_type', 'Interpretation'))}</b>: "
                    f"{safe_text(observation.get('description', ''))}<br/><i>Uncertainty: "
                    f"{safe_text(observation.get('uncertainty') or 'not recorded')}</i>",
                    body_style,
                ))
        else:
            elements.append(Paragraph("No machine-generated hypotheses or incident classifications are stored in this case timeline.", body_style))

        elements.append(Paragraph("7. Limitations and Uncertainty", h2_style))
        elements.append(Paragraph(
            "This report is generated by an academic prototype and has not been validated for legal or operational forensic use. "
            "AI detections, captions, transcripts, frame-change observations, and optional classifications may be wrong and require "
            "independent review against the original evidence. Media-relative timestamps from separate files are not synchronized. "
            "Missing observations do not establish that an event did not occur. Hashes alone do not establish chain of custody.",
            body_style,
        ))

        # Build document
        try:
            doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
        except Exception as exc:
            logger.error("PDF generation failed (%s).", type(exc).__name__)
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return {"status": "error", "error": "PDF generation failed; no partial report was kept."}

        logger.info("PDF report successfully written to %s", output_path)

        return {
            "status": "ok",
            "case_id": case_id,
            "output_path": str(output_path),
            "file_name": output_path.name,
            "file_size": output_path.stat().st_size,
            "observations_included": len(observations),
            "observations_omitted": 0,
            "hashes_included": len(hash_rows),
        }


report_service = ReportService.get_instance()
