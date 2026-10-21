# Proposed Solution: CrimeVision AI

## 1. Solution Overview
**CrimeVision AI** is an academic Flask prototype intended to help review image, audio, and video observations locally. It accepts media files, computes recorded digests, offers optional model analysis, stores observations in a case timeline, supports local keyword lookup, and generates prototype PDF summaries. It does not validate evidence integrity, synchronize separate recordings, or produce legally validated or court-admissible reports.

---

## 2. Subsystems & Current Implementation Notes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CRIMEVISION AI SOLUTION MODULES                       │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│ 1. VISUAL FORENSICS │ 2. AUDIO FORENSICS  │ 3. VIDEO FORENSICS              │
│ - RT-DETR Detection │ - Whisper ASR       │ - Keyframe Sampling (2s)        │
│ - BLIP Captioning   │ - Timestamp Chunking│ - IoU Bounding Box Tracking     │
│ - CLIP Zero-Shot    │ - Energy Fallback   │ - Monotonic Entity Track IDs    │
│ - Laplacian Blur Var│ - Acoustic Metrics  │ - Dynamic Tier Provenance       │
├─────────────────────┴─────────────────────┴─────────────────────────────────┤
│ 4. MULTIMODAL FUSION & TIMELINE CORE                                        │
│ - Cross-Modal Event Correlation                                             │
│ - JSON Flat-File Persistence (`data/<case_id>.json`)                         │
│ - Interactive Multi-Track SVG Timeline with Zoom/Pan                        │
├───────────────────────────────────────────┬─────────────────────────────────┤
│ 5. CASE OBSERVATION CHAT                  │ 6. ACADEMIC PROTOTYPE REPORT    │
│ - Scoped to selected case observations    │ - ReportLab PDF Generation      │
│ - Optional Groq after confirmation        │ - Recorded SHA-256 Digests      │
│ - Local keyword-based fallback            │ - Timeline and limitations      │
└───────────────────────────────────────────┴─────────────────────────────────┘
```

### Subsystem 1: Visual Forensics ([services/image_service.py](../src/services/image_service.py))
- **Object Detection**: Optional RT-DETR can return its model labels, boxes, and scores when available; pretrained inference has not been verified in the current audit.
- **Image Metrics**: Computes Laplacian variance and color-channel statistics as basic image measurements. These values do not establish tampering.
- **Fallback**: Candidate contour regions and rule-based descriptions are explicitly not semantic model detections.

### Subsystem 2: Audio Forensics ([services/audio_service.py](../src/services/audio_service.py))
- **Speech Transcription**: Optional local Whisper can return time-coded segments when its model is loaded; this model path has not been verified.
- **Acoustic Fallback**: When Whisper is unavailable, the service records acoustic measurements and does not produce fabricated transcript text, language, or speech timestamps.

### Subsystem 3: Video Forensics ([services/video_service.py](../src/services/video_service.py))
- **Keyframe Extraction**: Decodes video streams using OpenCV, extracting frames at fixed intervals (default: every 2 seconds).
- **Approximate Tracking**: IoU association is applied only to model-produced semantic detections. Track IDs indicate spatial continuity, not a person's identity; pretrained detection has not been verified.
- **Dynamic Tier Reporting**: The service records whether a neural or fallback analysis path ran; mocked detections and synthetic video are covered by tests.

### Subsystem 4: Cross-Modal Timeline Fusion ([services/fusion_service.py](../src/services/fusion_service.py))
- Ingests observations across modalities and records whether times are file-relative or unknown. Separate files are not synchronized.
- Stores case state in structured JSON files (`data/<case_id>.json`) for fast, zero-configuration local persistence.
- Renders an interactive SVG multi-track timeline ([static/js/timeline.js](../src/static/js/timeline.js)) with color-coded modality tracks, hover cards, and pan/zoom capabilities.

### Subsystem 5: Case Observation Q&A ([services/intelligence_service.py](../src/services/intelligence_service.py))
- Limits selected context to stored observations for the requested case. Citation checks and prompt boundaries reduce unsupported outputs but cannot eliminate hallucinations.
- Uses local keyword lookup by default. Optional Groq requests require confirmation; live Groq behavior is unverified.

### Subsystem 6: Academic Prototype PDF Report ([services/report_service.py](../src/services/report_service.py))
- Generates academic prototype PDF summaries using ReportLab.
- Includes recorded digests where available; digests do not certify file integrity, chain of custody, or admissibility.

---

## 3. Current Limitations & Planned Refinements
- **Facial Recognition**: Not implemented; no identity recognition should be inferred from the prototype's outputs.
- **Live Stream Decoding**: Video analysis operates on recorded files rather than live RTSP camera feeds.
- **Relational Backend**: The JSON flat-file store is optimized for academic and single-workstation use; enterprise deployment will require migration to SQLite/PostgreSQL.

---
*Reference Implementation Files:*
- [services/image_service.py](../src/services/image_service.py)
- [services/audio_service.py](../src/services/audio_service.py)
- [services/video_service.py](../src/services/video_service.py)
- [services/fusion_service.py](../src/services/fusion_service.py)
- [services/report_service.py](../src/services/report_service.py)
