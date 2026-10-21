# Problem-Solution Fit: CrimeVision AI

## 1. Executive Summary
This document maps the problems identified in Phase 1 to proposed CrimeVision AI features and records their current implementation limits. The application is an academic prototype; the listed features do not establish forensic validity or solve these operational problems in a validated environment.

---

## 2. Problem-Solution Mapping Matrix

| # | Identified Problem in Forensic Practice | Prototype Feature and Current Status | Specific Implementation Mechanism |
|---|---|---|---|
| **1** | **Multi-Modal Fragmentation**: Separate media files can make review difficult. | **Case Timeline (partial)**: Stores observations by evidence source. Separate file-relative times are not synchronized; the loopback demo displayed the timeline. | `FusionService.get_timeline()` in [services/fusion_service.py](../src/services/fusion_service.py) and [static/js/timeline.js](../src/static/js/timeline.js). |
| **2** | **Evidence Change Review**: Later byte comparison may be useful. | **SHA-256 Digests (implemented)**: Digests are recorded where generated and may support later comparison; they do not prevent modification or establish chain of custody. | [utils/file_utils.py](../src/utils/file_utils.py) and [services/report_service.py](../src/services/report_service.py). |
| **3** | **Video Review**: Long recordings can take substantial time to inspect. | **Sampling and Approximate Tracking (partial)**: Synthetic-video sampling is tested; detection depends on unverified optional model inference, and track IDs are not identities. | [services/video_service.py](../src/services/video_service.py); detector tests use mocked outputs. |
| **4** | **Audio Review**: Long recordings can take substantial time to inspect. | **Optional Whisper (partial)**: Timestamped transcript segments are produced only when Whisper is available; fallback behavior does not create transcript text. | [services/audio_service.py](../src/services/audio_service.py). |
| **5** | **AI Output Transparency**: Reviewers need to know which analysis path produced an observation. | **Provenance Fields (partially verified)**: The application labels neural and fallback paths; real neural inference was not tested. | Provenance fields in the modality services and [utils/evidence_schema.py](../src/utils/evidence_schema.py). |
| **6** | **Privacy**: Sensitive media should not be sent to external services by default. | **Local-First Core (partially verified)**: Core upload and report processing is local. Optional Groq requests require per-action confirmation and send selected text, not media files. | Local Flask app and opt-in handlers in `routes/` and `static/js/dashboard.js`. |

---

## 3. Scope of Impact & Realistic Operational Boundaries

To ensure academic and practical rigor, CrimeVision AI establishes clear operational boundaries:
1. **Academic Prototype**: Outputs are tentative software observations, not verified facts, legal findings, or guilt determinations.
2. **Unverified Model Paths**: RT-DETR, BLIP, CLIP, Whisper, and live Groq inference were not verified in this audit; accuracy and performance claims are not established.
3. **Fallback Limits**: Local fallback behavior differs by modality. In particular, the audio fallback produces acoustic measurements, not a transcript.

---
*Reference Implementation Files:*
- [services/fusion_service.py](../src/services/fusion_service.py)
- [services/report_service.py](../src/services/report_service.py)
- [utils/evidence_schema.py](../src/utils/evidence_schema.py)
