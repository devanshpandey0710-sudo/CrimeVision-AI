# Demonstration Plan: CrimeVision AI

## 1. Overview
This demonstration plan outlines the preparation checklist, sequence of events, anticipated outcomes, and contingency recovery procedures for presenting CrimeVision AI to evaluators and project review committees.

---

## 2. Pre-Demonstration Preparation Checklist

- [ ] **Python Environment**: Confirm virtual environment is activated (`(venv)` appears in terminal prompt).
- [ ] **Dependencies**: Verify core imports only; neural packages and weights are optional and need not be installed for a local fallback demo.
- [ ] **Port Availability**: Verify port 5000 is open (or set custom port in `.env`).
- [ ] **Case Context**: Create a new case ID such as `CASE-DEMO-FINAL`. Do not delete existing cases, uploads, or reports to prepare a demo.
- [ ] **Prepared Synthetic Media**:
  - Image: a self-created geometric test image such as `synthetic_scene.png`; no private or real-evidence image.
  - Optional audio/video: synthetic media only, if those modules are included in the presentation.
- [ ] **Browser Readiness**: Chrome, Firefox, or Edge updated and ready at `http://127.0.0.1:5000`.
- [ ] **Privacy**: Use a fresh synthetic case ID. Confirm the app is loopback-only, Groq is unconfigured or declined, and model downloads remain disabled.

---

## 3. Recommended Demonstration Sequence

```
[00:00 - 01:00]  1. Launch and dashboard overview
       │
[01:00 - 03:00]  2. Create a synthetic case and upload the permitted test image
       │
[03:00 - 05:00]  3. Review the actual analysis response and inference tier
       │
[05:00 - 06:30]  4. Inspect the evidence timeline and time-basis notice
       │
[06:30 - 08:00]  5. Open AI Chat; decline external processing and show local-only response
       │
[08:00 - 10:00]  6. Generate the PDF and explain its academic limitations
```

---

## 4. Expected Visible Outcomes by Module

| Module Demonstrated | Expected Visual Outcome | Key Metric to Highlight |
|---|---|---|
| **Health Endpoint** | Green health badge (`STATUS: ONLINE`). | Server is running locally on CPU. |
| **Image Analysis** | Show the returned `inference_source`, `inference_engine`, and semantic detection count. If the tier is heuristic, regions are candidates only. | Do not describe heuristic labels or scene categories as detected objects. |
| **Audio Analysis** | Transcript only if local Whisper is available. | Timestamps are audio-file-relative; no transcript is produced in fallback mode. |
| **Video Analysis** | Sampled keyframe gallery, motion-change observations, and tracks only for semantic detections. | Tracks are approximate spatial continuity, not identity. |
| **Timeline View** | SVG multi-track graph with observations grouped by source. | Separate media clocks are not synchronized. |
| **Evidence Chat** | Local keyword lookup; optional Groq after confirmation. | Check citation IDs; local keyword matching may miss related evidence. |
| **PDF Report** | Academic prototype report with source inventory, times, digests, and limitations. | Hashes do not establish custody or admissibility. |

---

## 5. Contingency & Recovery Procedures

| Potential Live Demo Issue | Underlying Cause | Quick Recovery Action |
|---|---|---|
| **Server fails to start** | Port 5000 occupied by another background task. | Launch from the repository root using: `.\src\launch.ps1 -Port 5050`. |
| **Optional Groq feature unavailable** | Groq is not configured or the service is unreachable. | Continue with local processing and explain that Groq is optional. |
| **Slow video processing** | High-resolution video with many frames on CPU. | Use a short clip (under 15 seconds) or set `VIDEO_FRAME_INTERVAL_SEC=4` in `.env`. |
| **Browser doesn't open automatically** | Pop-up blocker or default browser delay. | Manually open `http://127.0.0.1:5000` in any web browser. |

---
*Reference Implementation Files:*
- [launch.ps1](../src/launch.ps1)
- [desktop_launcher.bat](../src/desktop_launcher.bat)
- [config.py](../src/config.py)

## Screenshot Checklist

No screenshots were captured as part of the release verification. If recording the presentation, capture only after checking the visible content:

- [ ] Dashboard at loopback with no personal browser profile details or notifications visible.
- [ ] Synthetic case and image-analysis response, including inference tier and detection count.
- [ ] Timeline showing the source and relative-time limitations.
- [ ] AI Chat showing that a declined external request stayed local.
- [ ] Generated academic PDF with only synthetic case content.

Review every image and PDF for identifiers and metadata before deciding whether to publish it. Keep unreviewed captures out of Git.
