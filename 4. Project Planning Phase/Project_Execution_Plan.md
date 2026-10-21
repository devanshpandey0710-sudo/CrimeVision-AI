# Project Execution Plan: CrimeVision AI

## 1. Overview & Methodology
The development of CrimeVision AI followed an iterative engineering lifecycle. This plan clearly distinguishes between **documented historical milestones** (already verified in the codebase) and **proposed future enhancements**.

---

## 2. Documented Historical Milestones (Phases 1 through 8)

The following milestone sequence is derived from actual development logs ([DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md)) and verified project status records ([PROJECT_STATUS.md](../PROJECT_STATUS.md)):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 CRIMEVISION AI HISTORICAL DEVELOPMENT PHASES                │
├─────────┬────────────────────────────────────────┬──────────────────────────┤
│ PHASE   │ DELIVERABLE / SCOPE                    │ VERIFICATION ARTIFACT    │
├─────────┼────────────────────────────────────────┼──────────────────────────┤
│ Phase 1 │ Scaffolding, Flask Factory, Schemas    │ src/app.py, src/utils/   │
│ Phase 2 │ Environment and Model Integration      │ venv, src/requirements* │
│ Phase 3 │ Image Service and Fallbacks             │ src/services/image_service.py│
│ Phase 4 │ Audio Service and Fallback              │ src/services/audio_service.py│
│ Phase 5 │ Video Sampling and Tracking             │ src/services/video_service.py│
│ Phase 6 │ Timeline and JSON Case Store            │ src/services/fusion_service.py│
│ Phase 7 │ Academic Prototype PDF                  │ src/services/report_service.py│
│ Phase 8 │ Tests and Local Launch                  │ src/tests/, src/launch* │
└─────────┴────────────────────────────────────────┴──────────────────────────┘
```

> Verification note: the latest offline release run collected and passed 146 tests after the source was organized under `src/`. Earlier test counts in historical development notes are superseded. Passing tests do not establish model accuracy.

### Detailed Historical Milestones:
1. **Milestone 1: Project Scaffolding & Architecture**
   - Established Flask application factory pattern with blueprint isolation.
   - Built evidence schemas and cryptographic hashing utilities (`file_utils.py`).
2. **Milestone 2: Virtual Environment & Model Integration**
   - Set up Python virtual environment; pinned dependencies for PyTorch CPU, OpenCV, Whisper, Transformers.
3. **Milestone 3: Visual Forensics Engineering**
   - Added optional RT-DETR detection, BLIP captioning, and CLIP classification paths; RT-DETR was smoke-tested offline on a synthetic still, while BLIP/CLIP and real-evidence accuracy remain unverified.
   - Added Laplacian image-quality measurement and heuristic candidate-region behavior.
4. **Milestone 4: Acoustic Forensics Engineering**
   - Added an optional Whisper path for timestamped speech transcription; cached Whisper transcribed offline-generated speech through the service, while real-recording accuracy remains unverified.
   - The current fallback retains acoustic measurements and does not fabricate transcript text or speech timestamps.
5. **Milestone 5: Temporal Video Forensics & Entity Tracking**
   - Added bounded configurable keyframe sampling.
   - Added IoU association for semantic model detections; RT-DETR executed on three synthetic frames with zero detections, while real-video detection/tracking remains unverified.
   - Engineered dynamic tier reporting (`deep_learning` vs `heuristic_fallback`).
6. **Milestone 6: Multimodal Timeline Fusion**
   - Developed `FusionService` to aggregate visual, auditory, and video events into a chronological timeline.
   - Implemented interactive multi-track SVG timeline in `timeline.js`.
7. **Milestone 7: Academic Prototype PDF Generation**
   - Built a ReportLab prototype report generator.
   - Added available source digests and limitations; the report does not certify evidence integrity or chain of custody.
8. **Milestone 8: Test Suite & Launcher Files**
   - The latest offline release run passed 146 tests with model downloads disabled. This does not establish model accuracy.
   - Launcher files are present; their interactive runtime flows have not been manually verified.

---

## 3. Proposed Future Work & Roadmap

The following tasks represent prospective future development phases and are clearly labeled as planned enhancements:

| Planned Milestone | Description | Target Benefit |
|---|---|---|
| **Future Phase 9** | **Relational Database Migration** | Transition from JSON flat-files to an indexed SQLite / PostgreSQL store for enterprise multi-user concurrency. |
| **Future Phase 10** | **Live RTSP Stream Processing** | Enable real-time frame ingestion from live CCTV feeds and body-worn cameras. |
| **Future Phase 11** | **Local GGUF LLM Integration** | Embed quantized local LLMs (via `llama.cpp` / `ollama`) to eliminate external Groq API requirements completely. |
| **Future Phase 12** | **Redaction & Anonymization Engine** | Automated facial and license plate blurring for public disclosure compliance. |

---
*Reference Implementation Files:*
- [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md)
- [PROJECT_STATUS.md](../PROJECT_STATUS.md)
