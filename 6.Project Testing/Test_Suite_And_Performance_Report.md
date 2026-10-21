# Test Suite & Performance Report: CrimeVision AI

## 1. Overview & Verification Context
CrimeVision AI includes pytest tests for its Flask routes, services, schema, timeline, and PDF generator. The latest release verification ran after moving the application into `src/`, using the existing Python 3.14.8 environment. `.env` loading and model downloads were disabled, Groq was unconfigured, and test output paths were isolated from existing case data. No dependencies or model weights were installed or downloaded for this run.

---

## 2. Actual Test Execution Results

**Command Executed** (all collected tests were run with model access offline):
```powershell
$env:PYTHON_DOTENV_DISABLED = '1'
$env:ALLOW_MODEL_DOWNLOADS = '0'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:GROQ_API_KEY = $null
$env:DATA_FOLDER = '..\.audit-final-suite\data'
$env:UPLOAD_FOLDER = '..\.audit-final-suite\uploads'
$env:REPORTS_FOLDER = '..\.audit-final-suite\reports'
$env:PYTHONDONTWRITEBYTECODE = '1'
..\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

**Verified Test Outcome Summary:**
```text
146 tests collected
146 passed in 17.68s
```

The suite includes synthetic multimodal report checks, route failure-state checks, and a local-chat assertion that uncertainty and heuristic limitations remain explicit. During an earlier loopback browser smoke run, before the final chat-history privacy hardening, a generated geometric test image produced a heuristic fallback with zero semantic detections; the timeline, consent-declined local chat, and PDF workflow were exercised. The PDF download endpoint returned a valid PDF signature. The final chat-history change is covered by the latest automated suite; the browser flow was not replayed afterward. No screenshots were saved.

### Previously recorded synthetic model smoke checks (not repeated in this release pass)

- Earlier project notes record offline checks using locally cached model files; those checks were not independently repeated during this release pass.
- RT-DETR processed a generated 640×480 PNG through ImageService: status `ok`, deep-learning path, one detection, and two synthetic-case observations.
- RT-DETR processed three sampled frames from a generated AVI through VideoService: all three used the deep-learning path, with zero detections per frame. The service returned `ok` and persisted one synthetic video summary.
- Cached Whisper processed a generated one-second silent 16 kHz WAV through AudioService: status `ok`, deep-learning path, zero speech segments, and one synthetic-case summary. No speech was expected from silence.
- Windows offline speech synthesis generated a 16 kHz mono test WAV. Cached Whisper transcribed it as “The red car is near the building.”; AudioService persisted one speech segment from 0.0 to 2.0 seconds.
- SciPy 1.18.1 in the isolated audit environment converted a generated 48 kHz stereo WAV to 16 kHz mono float samples (16,000 samples); no audio content was sent externally.
- BLIP and CLIP were disabled in those recorded checks because their model weights were not cached. These synthetic checks do not measure model accuracy or performance on real evidence. In the current browser demo RT-DETR was unavailable and the service reported `heuristic_fallback`; it returned zero semantic detections.

### PDF download and rendered-layout check

- The Flask test-client test generated a report from one synthetic image observation with a synthetic SHA-256 value, then downloaded it through the API. It passed MIME type, attachment filename, and PDF signature checks.
- Poppler identified the report as two landscape Letter pages. Visual review showed readable metadata, the evidence inventory, timeline, SHA-256 row, limitations, and page footers without clipping or overlap.
- Poppler emitted missing display-font warnings for Symbol and Arial Unicode; the rendered ASCII test content remained legible. Non-ASCII evidence text was not tested.
- A separate 46-observation synthetic report rendered as six pages. All 46 observations, including the final timeline row, appear in the PDF with the recorded processing engine/tier and analysis timestamp; the case data still contains all 46. Visual review found no clipping or overlap.

### Analysis failure-state route checks

- Three synthetic Flask-client cases force the image, audio, and video analysis services to return an error.
- Each endpoint now returns HTTP 422 with its error payload, allowing the dashboard's existing HTTP-status check to render a failure state instead of a success state.
- The tests use an isolated temporary upload folder and do not load models or use existing evidence.
- The full suite also verifies the PDF includes the full timeline across multiple pages and displays recorded processing engine/tier metadata.

---

## 3. Test Coverage Breakdown by Module

| Test Module | Behaviors covered in current suite |
|---|---|
| [tests/test_app.py](../src/tests/test_app.py) | Flask startup, health/dashboard endpoints, upload and route validation, CORS, local-only chat default, truthful image/audio/video service failure responses, PDF generation and download response. |
| [tests/test_case_paths.py](../src/tests/test_case_paths.py) | Case ID validation and path containment. |
| [tests/test_image_service.py](../src/tests/test_image_service.py) | Observation schema, image validation, corrupt inputs, truthful fallback output, and non-overwriting annotated-image writes. |
| [tests/test_audio_service.py](../src/tests/test_audio_service.py) | Audio fallback, acoustic analysis, timeline insertion, and decoded 16 kHz WAV samples passed to Whisper without FFmpeg. |
| [tests/test_video_service.py](../src/tests/test_video_service.py) | Synthetic AVI processing, frame limits, corrupt inputs, candidate-region semantics, and motion observations. |
| [tests/test_intelligence_service.py](../src/tests/test_intelligence_service.py) | Mocked image/audio/video model output, excerpt/citation checks, source timestamp copying, and unavailable paths. |
| [tests/test_image_routes.py](../src/tests/test_image_routes.py) | Image hypothesis consent, Groq-unavailable behavior, and filtering to the selected image's stored observations. |
| [tests/test_chat_service.py](../src/tests/test_chat_service.py) | Local default, case isolation, prompt boundaries, citation validation, and no transmission of prior local chat history. |
| [tests/test_fusion_service.py](../src/tests/test_fusion_service.py) | Persistence, source-relative sorting, exact duplicate suppression, conflict preservation, and cross-file correlation safeguards. |
| [tests/test_phase2.py](../src/tests/test_phase2.py) | SHA-256 helpers, provenance fields, IoU math, and tracking with a mocked detector. |
| [tests/test_reports.py](../src/tests/test_reports.py) | PDF compilation, digest output, absent hashes, hostile-text escaping, and existing-report preservation. |

---

## 4. Distinction Between Functional Tests and Performance Claims

To maintain academic rigor:
1. **Functional tests:** All 146 checks exercise application logic, input errors, privacy boundaries, schema and timeline behavior, mocked model responses, media routes, PDF generation, video-service readiness, and default no-download model loading.
2. **Model limits:** Offline checkpoint tests verify that missing weights do not trigger downloads. The current browser image demonstration used the heuristic fallback and returned zero semantic detections; synthetic checks do not establish real-evidence accuracy.
3. **Timing:** 17.68 seconds is the elapsed time for this one test run from the clean release copy, not a performance benchmark. No FPS, throughput, or real-model latency is claimed.

---
*Reference Implementation Files:*
- [tests/test_app.py](../src/tests/test_app.py)
- [tests/test_phase2.py](../src/tests/test_phase2.py)
- [tests/test_reports.py](../src/tests/test_reports.py)

## Current Release-Packaging Audit Note

The 146-test result above is a previously recorded run, not a result reproduced during the later packaging audit. In that audit environment, pytest was unavailable and no packages were installed. Before making a new test claim for a changed release, install the declared test requirements in a suitable isolated environment and rerun the suite. No new test pass is claimed by this note.
