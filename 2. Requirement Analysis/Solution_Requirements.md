# Solution Requirements: CrimeVision AI

## 1. Overview
This document specifies the functional, non-functional, security, and fallback requirements for the CrimeVision AI platform. Requirements are clearly categorized into verified production behaviors and planned enhancements.

---

## 2. Functional Requirements (FR)

| Req ID | Requirement Description | Module | Verification Status |
|---|---|---|---|
| **FR-01** | The system shall compute a cryptographic SHA-256 hash immediately upon file upload and persist it alongside all observations. | Ingestion / File Utils | **Verified** ([utils/file_utils.py](../src/utils/file_utils.py)) |
| **FR-02** | The system shall validate uploaded files using magic bytes in addition to file extension checking to prevent trivial format spoofing. | Ingestion / File Utils | **Verified** ([utils/file_utils.py](../src/utils/file_utils.py)) |
| **FR-03** | The system shall detect objects in images and compute blur metrics (Laplacian variance) and color channel statistics. | Vision Service | **Partially verified** ([services/image_service.py](../src/services/image_service.py)): image metrics/fallbacks are tested and RT-DETR returned one detection on a synthetic still; real-evidence accuracy remains unverified. |
| **FR-04** | The system shall transcribe speech recordings into time-coded segments using Whisper ASR (or acoustic energy segmentation fallback). | Audio Service | **Partially met** ([services/audio_service.py](../src/services/audio_service.py)): cached Whisper transcribed offline-generated speech and the service persisted one timestamped segment; a synthetic 48 kHz stereo file was resampled to 16 kHz mono; real-recording accuracy and broad format support remain unverified. |
| **FR-05** | The system shall sample video frames at configurable intervals, detect visual entities, and track them across frames using IoU matching with monotonic `track_id` assignments. | Video Service | **Partially verified** ([services/video_service.py](../src/services/video_service.py)): RT-DETR executed on three sampled synthetic frames but returned zero detections; mocked tracking tests pass, real-video detection and tracking remain unverified. |
| **FR-06** | The system shall correlate observations across visual, audio, and video modalities into a unified chronological case timeline. | Fusion Service | **Partially verified** ([services/fusion_service.py](../src/services/fusion_service.py)): timeline persistence and source-aware ordering are tested; timestamps from separate files are not synchronized. |
| **FR-07** | The system shall provide a natural-language Q&A interface strictly grounded in recorded case facts, falling back to rule-based synthesis if the LLM API is unavailable. | Intelligence / Chat | **Partially verified** ([services/chat_service.py](../src/services/chat_service.py)): local keyword lookup and mocked citation/consent behavior are tested; live Groq behavior and semantic retrieval are unverified. |
| **FR-08** | The system shall generate a downloadable, structured academic prototype PDF with case/evidence identifiers, analysis and generation times, source inventory, modality summaries, unified timeline, processing metadata, machine-generated interpretations, limitations, and uncertainty. | Report Service | **Verified as an academic prototype** ([services/report_service.py](../src/services/report_service.py)): API download and PDF sections are covered by tests; the PDF is explicitly not legally validated or court-ready. |

---

## 3. Non-Functional Requirements (NFR)

| Req ID | Category | Requirement Specification | Actual Implementation Status |
|---|---|---|---|
| **NFR-01** | **Local-First** | All file processing, timelines, and reporting shall function without requiring an internet connection or external cloud storage. | **Partially verified**: core install, local health endpoint, and fallback behavior have automated coverage; model weights are local-only by default. Optional Groq requires external access and was not live-tested. |
| **NFR-02** | **CPU Compatibility** | The platform shall execute on standard commodity workstation CPUs (e.g. 8–16 GB RAM) without mandatory CUDA/GPU hardware. | **Partially verified**: the core runs without Torch/CUDA and synthetic tests pass locally; resource use and pretrained CPU inference have not been measured. |
| **NFR-03** | **Modularity** | AI services shall follow a singleton pattern with lazy loading so the application starts instantly without blocking on model downloads. | **Partially verified**: startup/health checks do not load models; default model loading is restricted to local checkpoints and automated tests prove a missing Whisper checkpoint does not trigger a download. Cached RT-DETR/Whisper smoke checks use synthetic media. |
| **NFR-04** | **Observability** | Every observation shall explicitly tag its execution provenance (`deep_learning` vs `heuristic_fallback`) so analysts know the exact origin of every finding. | **Partially verified**: provenance fields and mocked/fallback behavior have automated coverage; actual neural inference provenance was not checked. |

---

## 4. Error Handling & Fallback Behavior

```
               ┌─────────────────────────────────────┐
               │    MODALITY INFERENCE REQUEST       │
               └──────────────────┬──────────────────┘
                                  │
                   Are deep learning models loaded?
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
                  [YES]                        [NO]
                    │                           │
          Execute Torch / HF /           Log warning & invoke
          Whisper Neural Models          Heuristic Fallback Engine
                    │                           │
           Tag Provenance as:            Tag Provenance as:
            "deep_learning"             "heuristic_fallback"
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                Return Standardized Observation Record
                (Contains SHA-256, timestamps, confidence)
```

1. **Vision Fallback**: When pretrained vision models are unavailable, the service can return heuristic candidate regions and rule-based descriptions; these are not semantic detections or verified model captions.
2. **Audio Fallback**: When Whisper is unavailable, the service returns acoustic measurements and does not fabricate transcript text, language, or speech timestamps.
3. **Video Fallback**: Frame differences can produce tentative motion-change observations. Heuristic contours are not tracked or reported as identified entities.
4. **LLM Fallback**: When Groq is unavailable, chat uses local keyword-ranked observations and a rule-based response. This is not semantic search. Mocked external-response behavior is tested; live Groq behavior is unverified.

---

## 5. Security & Privacy Considerations
- **No Secret Exposure**: Real API keys and passwords are read solely from `.env` and never logged or serialized into client-facing JSON.
- **Evidence Isolation**: Evidence directories (`uploads/`, `reports/`, `data/`) are excluded from version control via `.gitignore`.
- **Integrity Validation**: SHA-256 digests support later byte-for-byte comparisons. They do not prevent changes to files or establish chain of custody.

---
*Reference Implementation Files:*
- [config.py](../src/config.py)
- [utils/file_utils.py](../src/utils/file_utils.py)
- [services/intelligence_service.py](../src/services/intelligence_service.py)
