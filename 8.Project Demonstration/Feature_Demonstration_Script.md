# Feature Demonstration Script: CrimeVision AI

## 1. Safety & Demonstration Guidelines
- **Strict Evidence Rule**: Never use actual crime scene evidence, unredacted surveillance video, or private investigatory records during demonstrations.
- **Synthetic Demonstration Assets**: Use self-created or otherwise approved synthetic media. Do not describe generic or heuristic outputs as verified findings.
- **Environment**: Ensure the local virtual environment is active and the application is running at `http://127.0.0.1:5000`.

---

## 2. Step-by-Step Live Demonstration Walkthrough

### Step 1: Launch and Health Verification
1. Open PowerShell and run:
   ```powershell
   .\src\launch.ps1
   ```
2. The browser automatically navigates to `http://127.0.0.1:5000`.
3. Highlight the **System Health Badge** in the top navigation bar showing `STATUS: ONLINE` and the active model fallback indicators.

### Step 2: Case Inception & Case ID Assignment
1. In the sidebar, enter a new case identifier:
   ```text
   DEMO-SYNTHETIC-01
   ```
2. Explain that observations are stored locally in `src/data/DEMO-SYNTHETIC-01.json`. The current JSON write is not atomic; use synthetic data for this demo.

### Step 3: Visual Evidence Ingestion & Blur Detection
1. Select the **Image Analysis** module.
2. Upload a self-created synthetic image (for example, geometric shapes saved as `synthetic_scene.png`).
3. Click **Analyze Image**.
4. Show the audience:
   - The SHA-256 digest and image-quality measurements returned in the analysis JSON.
   - Semantic detections and annotated image only if RT-DETR actually ran. Otherwise explain that contour regions are candidates, not identified objects.
   - The `inference_source`, `inference_engine`, detection count, and uncertainty. Do not present heuristic categories or scores as identified objects.

### Step 4: Audio Evidence Ingestion & Whisper Transcription
1. Select the **Audio Analysis** module.
2. Upload an approved synthetic audio sample (if audio is included in the demonstration).
3. Click **Transcribe Audio**.
4. Show the audience:
   - The SHA-256 hash generated for the audio stream.
   - Whisper transcript segments only if local Whisper is available. Times are relative to the audio file; when unavailable, the UI must show no transcript.
   - Candidate-event extraction is optional. Confirm before any transcript text is sent to Groq.

### Step 5: Video Keyframe Sampling & IoU Entity Tracking
1. Select the **Video Analysis** module.
2. Upload an approved synthetic video clip (if video is included in the demonstration).
3. Click **Process Video**.
4. Show the audience:
   - The extracted keyframes sampled every 2 seconds.
   - Bounding boxes and approximate `track_id` values only if RT-DETR semantic detections are produced. Otherwise show the sampled frames and explain that heuristic regions are not object detections.

### Step 6: Interactive Multi-Track SVG Timeline
1. Switch to the **Timeline View** on the dashboard.
2. Demonstrate:
   - The multi-track view and its notice that timestamps are file-relative and are not synchronized across separate evidence files.
   - Using the **Zoom In / Zoom Out** buttons.
   - Hovering over event points to reveal metadata cards with confidence scores and SHA-256 hashes.

### Step 7: Grounded AI Evidence Chat
1. Open **AI Chat**.
2. Decline the external-processing confirmation to keep the question and evidence context local. Ask:
   ```text
   What observations are stored for this case, and what uncertainty is recorded?
   ```
3. Observe the response:
   - Check that the response is labelled local-only and citations reference actual stored event IDs. Treat any optional hypotheses as tentative and review their uncertainty.
   - The local fallback uses keyword matching and may miss semantically related observations.

### Step 8: Generating the Academic Prototype PDF Report
1. Click **Generate PDF Report**.
2. Download and open the report for `DEMO-SYNTHETIC-01`.
3. Review the generated report's case identifier, evidence summaries, timestamps, provenance, limitations, and SHA-256 values where present.
4. Explain that a hash can help check whether file bytes changed; this report is not legally validated and does not establish chain of custody or admissibility.

---
*Reference Implementation Files:*
- [templates/index.html](../src/templates/index.html)
- [static/js/dashboard.js](../src/static/js/dashboard.js)
- [services/report_service.py](../src/services/report_service.py)
