# Feature Inventory: CrimeVision AI

## 1. Overview
This document catalogs all functional and technical features of the CrimeVision AI platform. To maintain academic and technical integrity, every feature is explicitly classified as **Implemented (Verified in Code)**, **Partially Implemented**, or **Planned (Roadmap)**.

---

## 2. Feature Classification Table

| Feature Name | Category | Implemented Status | Verification Source | Actual Implemented Behavior |
|---|---|---|---|---|
| **MIME & Magic-Byte Validation** | Security / Ingestion | **Implemented (basic)** | [utils/file_utils.py](../src/utils/file_utils.py) | Checks supported file signatures against extensions; this can reject simple mismatches but is not malware scanning or proof of file origin. |
| **Local-Only Model Loading by Default** | Privacy / Model Runtime | **Implemented and tested** | [config.py](../src/config.py), [services/image_service.py](../src/services/image_service.py), [services/audio_service.py](../src/services/audio_service.py) | Hugging Face loads use `local_files_only`; Whisper requires a cached checkpoint whose hash matches before loading. Missing weights use fallbacks; downloading requires explicit opt-in. |
| **SHA-256 Digesting** | Integrity / Forensics | **Implemented** | [utils/file_utils.py](../src/utils/file_utils.py) | Computes 64-char hexadecimal SHA-256 hash upon ingestion; persists in observations. |
| **Laplacian Blur Detection** | Image Forensics | **Implemented** | [services/image_service.py](../src/services/image_service.py) | Evaluates Laplacian variance; flags images with variance < 100.0 as potentially blurred. |
| **RT-DETR Object Detection** | Image Forensics | **Partially implemented** | [services/image_service.py](../src/services/image_service.py) | Offline smoke check returned one detection on a synthetic still. Real-evidence accuracy and optional BLIP/CLIP behavior remain unverified. Heuristic regions are not semantic object detections. |
| **BLIP Image Captioning** | Image Forensics | **Partially implemented** | [services/image_service.py](../src/services/image_service.py) | Optional loader and caption path exist; real model output has not been verified. |
| **CLIP Zero-Shot Classifier** | Image Forensics | **Partially implemented** | [services/image_service.py](../src/services/image_service.py) | Optional classifier path exists; real model output has not been verified. Rule-based fallback labels are candidate categories only. |
| **Whisper Speech-to-Text** | Audio Forensics | **Partially implemented** | [services/audio_service.py](../src/services/audio_service.py) | Cached Whisper transcribed an offline-generated speech sample and persisted one timestamped segment. Real-recording accuracy remains unverified; fallback produces no fabricated transcript. |
| **Keyframe Interval Sampling** | Video Forensics | **Partially implemented** | [services/video_service.py](../src/services/video_service.py) | Tested on synthetic AVI; samples at a configurable interval, limits frames and pixel dimensions, and writes reduced-size frames. Codec coverage is not exhaustive. |
| **IoU Entity Tracking** | Video Forensics | **Partially implemented** | [services/video_service.py](../src/services/video_service.py) | Approximate spatial association is tested with mocked detections; it runs only on semantic detections and does not identify people. |
| **Audio candidate event extraction** | Audio Forensics | **Partially implemented** | [services/intelligence_service.py](../src/services/intelligence_service.py) | Explicitly requested optional Groq flow validates transcript excerpts and copies timestamps from source segments; tested with mocked responses only. |
| **Dynamic Tier Provenance** | Observability | **Implemented** | [services/video_service.py](../src/services/video_service.py) | Aggregates frame-level inference to report `deep_learning` vs `heuristic_fallback` honestly. |
| **JSON Case Persistence** | Storage | **Partially implemented** | [services/fusion_service.py](../src/services/fusion_service.py) | Stores case timeline observations in JSON flat-files (`data/<case_id>.json`); writes are not atomic and require future hardening. |
| **SVG Multi-Track Timeline** | Presentation | **Partially implemented** | [static/js/timeline.js](../src/static/js/timeline.js) | Renders an interactive timeline; the loopback demo displayed it. File-relative timestamps remain unsynchronized across different source files. |
| **Grounded AI Evidence Chat** | Synthesis / LLM | **Partially implemented** | [services/chat_service.py](../src/services/chat_service.py) | Local keyword-based lookup is tested; optional Groq is confirmation-gated and mocked in tests. Live LLM behavior is unverified. |
| **Evidence Integrity PDF Table** | Reporting | **Implemented (prototype)** | [services/report_service.py](../src/services/report_service.py) | Includes recorded SHA-256 values where available in an academic prototype report; digests do not certify integrity or chain of custody. |
| **Cross-Platform Launchers** | Tooling | **Present; runtime unverified** | `launch.bat`, `launch.ps1`, `desktop_launcher.bat` | Launcher files exist, but launcher flows have not been manually checked in this audit. |
| **Speaker Diarization** | Audio Forensics | *Partially Implemented* | [config.py](../src/config.py) (`ENABLE_SPEAKER_DIARIZATION=0`) | Feature flag exists; requires heavy external pyannote pipelines; currently disabled by default. |
| **Relational Database Store** | Architecture | *Planned / Roadmap* | [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md) | Migration from JSON flat-files to SQLite or PostgreSQL for enterprise multi-tenancy. |
| **RTSP Live Stream Ingestion** | Video Forensics | *Planned / Roadmap* | [PROJECT_STATUS.md](../PROJECT_STATUS.md) | Real-time frame decoding from live IP cameras. |

---

## 3. Forensic Evidentiary Caveats & Ethical Boundaries
- **Admissibility**: CrimeVision AI is an academic prototype. Hash values and provenance fields alone do not establish evidence integrity, chain of custody, or legal admissibility.
- **No Autonomous Guilt Attributions**: The prototype is not designed to determine guilt. Prompt and output checks reduce unsupported claims in tested paths, but all generated descriptions and interpretations require human review.

---
*Reference Implementation Files:*
- [PROJECT_STATUS.md](../PROJECT_STATUS.md)
- [services/report_service.py](../src/services/report_service.py)
- [utils/file_utils.py](../src/utils/file_utils.py)
