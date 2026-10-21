# Stakeholder Communication: CrimeVision AI

## 1. Overview
Presenting this academic prototype requires clear limits. Do not describe it as legally validated, synchronized across separate recordings, or suitable for real investigations without further independent validation.

---

## 2. Communication Strategy by Stakeholder Audience

### Audience 1: Technical & Academic Evaluators
- **Core Message**: CrimeVision AI is a local Flask prototype with image, audio, video, timeline, chat, and report workflows. Cached RT-DETR and Whisper paths ran on synthetic inputs; real-evidence accuracy remains unverified.
- **Key Talking Points**:
  - Flask Application Factory with decoupled Blueprints for each evidentiary modality.
  - Service modules record which inference tier ran; contour regions are not described as semantic detections.
  - The latest offline automated run was 146 passed (146 collected); model accuracy was not tested.

### Audience 2: Forensic Analysts & Investigating Officers
- **Core Message**: CrimeVision AI groups observations from image, audio, and video uploads in a case timeline. File-relative times from separate files are not synchronized.
- **Key Talking Points**:
  - Recorded SHA-256 values can support later byte comparisons but do not establish chain of custody.
  - Video keyframes and approximate spatial tracking are available; tracking does not identify a person.
  - Cached Whisper transcribed an offline-generated speech sample into a timestamped segment; real-recording accuracy and broad audio-format support remain unverified.
  - Local chat uses keyword lookup; optional Groq requires per-action confirmation and outputs require human review.

### Audience 3: Legal & Judicial Stakeholders
- **Core Message**: CrimeVision AI is an academic prototype, not a validated decision-support tool. It does not replace human investigator discretion or offer autonomous determinations of guilt.
- **Key Talking Points**:
  - Prototype reports list recorded digests where present and explicitly disclaim legal validation.
  - Evidence is stored locally by default. Optional Groq actions can send the current question or selected transcript/observation text after confirmation; media files and earlier local chat history are not sent by chat.
  - Reports are not chain-of-custody records or legal findings.

---

## 3. Recommended Presentation Structure (10–15 Minute Demo)

| Time | Slide / Demonstration Focus | Live Demonstration Action |
|---|---|---|
| **0:00 – 2:00** | Problem Statement & Forensic Ingestion | Show current pain points of fragmented evidence; introduce local-first architecture. |
| **2:00 – 4:00** | Intake & File Digest | Upload a self-created synthetic image; show the actual inference tier, detection count, digest, and image-quality metrics. |
| **4:00 – 7:00** | Audio Transcription & Video Sampling | Show transcript only if Whisper runs; show sampled frames and approximate tracks only when semantic detections are available. |
| **7:00 – 10:00**| Timeline & Local/Optional Chat | Explain that separate file clocks are not synchronized; choose local chat or explicitly confirm an optional Groq request. |
| **10:00 – 12:00**| Academic Prototype PDF Export | Review the generated summary, source IDs, timestamps, digests, and limitations; do not call it court-admissible. |
| **12:00 – 15:00**| Q&A & Test Scope | Report 146 passed (146 collected); explain the current heuristic fallback and that real-evidence accuracy remains unverified. |

---
*Reference Implementation Files:*
- [services/report_service.py](../src/services/report_service.py)
- [static/js/timeline.js](../src/static/js/timeline.js)
- [tests/](../src/tests/)
