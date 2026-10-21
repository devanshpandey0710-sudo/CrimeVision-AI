# System Manual: CrimeVision AI

## 1. System Overview
**CrimeVision AI** is an academic Flask prototype for local image, audio, and video analysis workflows. It records file digests, optional model outputs, heuristic observations, a case timeline, local evidence lookup, and PDF summaries. It is not a legally validated forensic system; model inference is optional and has not been verified in the current audit.

---

## 2. Component Architecture & Core Workflows

```
                           ┌──────────────────────────┐
                           │      WEB BROWSER UI      │
                           │ (HTML5 / CSS3 / ES6 JS)  │
                           └─────────────┬────────────┘
                                         │
                                  REST API (JSON)
                                         │
                           ┌─────────────▼────────────┐
                           │    FLASK APPLICATION     │
                           │   (7 Blueprint Modules)  │
                           └─────────────┬────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌───────────────┐                ┌───────────────┐                ┌───────────────┐
│ ImageService  │                │ AudioService  │                │ VideoService  │
│ optional AI   │                │ optional AI   │                │ sampled frames│
└───────┬───────┘                └───────┬───────┘                └───────┬───────┘
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         ▼
                         ┌───────────────────────────────┐
                         │         FusionService         │
                         │ (Timeline & JSON Persistence) │
                         └───────────────┬───────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
         ┌───────────────────────────────┐ ┌───────────────────────────────┐
         │      IntelligenceService      │ │         ReportService         │
         │ (Groq only after confirmation│ │ (ReportLab prototype reports)│
         │     / local keyword lookup)  │ │                               │
         └───────────────────────────────┘ └───────────────────────────────┘
```

---

## 3. REST API Reference

The following paths are registered by the current Flask application. Upload routes use multipart form fields `file` and `case_id`; IDs are validated before file paths are built.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health and non-secret configuration summary |
| `GET` | `/api/models/status` | Model availability status; does not prove inference quality |
| `GET` | `/api/cases` | List local case IDs |
| `POST` | `/api/image/analyse` | Upload and analyze one image |
| `GET` | `/api/image/annotated/<evidence_id>` | Serve an annotated image only when semantic model detections were saved |
| `POST` | `/api/audio/transcribe` | Upload and analyze audio; transcript is empty if Whisper is unavailable |
| `POST` | `/api/audio/events` | Optional Groq candidate-event extraction from stored transcript text |
| `POST` | `/api/video/analyse` | Upload, sample, and analyze video frames |
| `GET` | `/api/video/keyframes/<evidence_id>/<filename>` | Serve a sampled keyframe |
| `POST` | `/api/video/classify` | Optional Groq classification of stored video observations |
| `GET` | `/api/evidence/timeline/<case_id>` | Read the unified case timeline |
| `DELETE` | `/api/evidence/case/<case_id>` | Delete local case JSON; use cautiously because this removes case records |
| `POST` | `/api/chat/ask` | Ask about one case; `allow_external` defaults to `false` |
| `GET` / `DELETE` | `/api/chat/history/<case_id>` | Read or clear in-memory chat history for that case |
| `POST` | `/api/report/generate` | Generate a local academic prototype PDF report |
| `GET` | `/api/report/download/<case_id>` | Download an existing local PDF report |

Dashboard confirmations are required before optional Groq routes receive transcript/evidence text. Calling those API routes directly is an explicit external request by the API caller.

---

## 4. Observation Data Schema ([utils/evidence_schema.py](../src/utils/evidence_schema.py))

New observations written to `src/data/<case_id>.json` use this shared schema. Some fields may be empty or unknown; older records may not contain the timestamp-basis field.

```json
{
  "event_id": "string (UUID)",
  "case_id": "string",
  "source_evidence_id": "string (upload identifier)",
  "modality": "image | audio | video",
  "timestamp_start": 12.5,
  "timestamp_end": 13.0,
  "timestamp_basis": "media_relative | wall_clock | unknown",
  "event_type": "speech_segment",
  "description": "Machine transcription; verify against original audio.",
  "source_reference": "segment_1",
  "confidence": 0.92,
  "uncertainty": "Machine transcription may be wrong.",
  "detected_objects": [],
  "metadata": {"sha256": "<64-character digest when available>", "inference_tier": "deep_learning | heuristic_fallback"},
  "created_at": "ISO-8601 UTC timestamp"
}
```

---

## 5. Security, Evidence Protection, and Privacy Controls
1. **Local by default**: The built-in development server binds to `127.0.0.1`. Files in `src/uploads/`, `src/reports/`, and `src/data/` persist on the host until manually removed. The app has no route authentication; do not expose it to a network or use it as a multi-user service.
2. **Optional external processing**: Groq is disabled unless configured. The dashboard asks before sending transcript text, the current chat question with selected observations, or video observation descriptions; direct API callers are responsible for their own consent. Chat requests do not include earlier local chat history, and the media files themselves are not sent by these optional flows.
3. **Git exclusions**: `.gitignore` excludes `.env`, `src/uploads/`, `src/reports/`, `src/data/`, model weights, and test audit folders by default. Git ignore rules do not prevent a forced add, so review `git status` before any future staging.
4. **Secrets and limitations**: Health/status responses do not expose the API key. This is a prototype; local persistence is not encrypted, and deleting a case JSON file does not remove uploaded evidence or generated reports.

---
*Reference Implementation Files:*
- [app.py](../src/app.py)
- [routes/](../src/routes/)
- [utils/evidence_schema.py](../src/utils/evidence_schema.py)
- [config.py](../src/config.py)
