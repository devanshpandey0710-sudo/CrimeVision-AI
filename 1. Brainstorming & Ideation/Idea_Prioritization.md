# Idea Prioritization: CrimeVision AI

## 1. Problem Discovery
In contemporary forensic analysis and criminal investigations, digital evidence is rarely confined to a single format. Modern investigations typically encompass:
- CCTV surveillance and smartphone video footage.
- Intercepted audio recordings, emergency dispatch calls, and witness voice notes.
- High-resolution crime scene photographs, forensic autopsy images, and document scans.

Currently, investigation units examine these modalities in silos using disparate, disconnected tools. An image analyst examines JPEG artifacts, an audio technician reviews spectrograms, and a detective reviews narrative chronologies. This siloed workflow causes several critical bottlenecks:
1. **Critical Cross-Modal Blindspots**: Correlating an audio event (e.g., sound of glass breaking at 02:14:05) with visual motion (e.g., an unidentified vehicle leaving an alley at 02:14:08) requires manual time-stamping, which is error-prone and labor-intensive.
2. **Chain of Custody and Evidence Integrity Risks**: Unstandardized file handling risks evidentiary tampering or inadmissibility unless cryptographically verifiable digests (e.g., SHA-256) are calculated immediately at ingestion.
3. **Investigation Fatigue and Cognitive Overload**: Reviewing hundreds of hours of raw footage and audio leads to analytical fatigue, missed corroborating clues, and delayed judicial processing.

---

## 2. Forensic Evidence-Analysis Challenges

| Challenge | Traditional Approach | Consequence / Limitation |
|---|---|---|
| **Disparate Modalities** | Separate proprietary tools for video, audio, and stills. | Inability to cross-reference timestamps across channels in real time. |
| **Evidence Tampering & Integrity** | Manual hash logging or post-facto verification. | Inconsistent audit trails and vulnerability to legal challenge. |
| **Entity Re-Identification** | Manual review of frame-by-frame suspect appearances. | High labor cost and failure to maintain entity tracking across camera blindspots. |
| **Cognitive Synthesis** | Manual aggregation of sticky notes, spreadsheets, and Word documents. | Fragmented timelines and lack of grounded, queryable investigative intelligence. |

---

## 3. Motivation for a Multimodal Platform
The core motivation behind **CrimeVision AI** is to provide an integrated, local-first multimodal forensic workstation that unifies vision, audio, temporal tracking, and structured reporting under an auditable investigative framework.

```
       ┌───────────────────────────────────────────────────────────┐
       │                   MULTIMODAL EVIDENCE INTAKE              │
       │         (Images, Audio Recordings, Video Footage)         │
       └─────────────────────────────┬─────────────────────────────┘
                                     │
                        Cryptographic Ingestion (SHA-256)
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
   ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
   │  VISUAL TIER  │         │  AUDIO TIER   │         │  VIDEO TIER   │
   │  (RT-DETR /   │         │ (Whisper ASR /│         │ (Sampling /   │
   │  BLIP / CLIP) │         │  Acoustics)   │         │ IoU Tracking) │
   └───────┬───────┘         └───────┬───────┘         └───────┬───────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     ▼
                      ┌──────────────────────────────┐
                      │    FUSION & TIMELINE CORE    │
                      │  Chronological Normalization │
                      └──────────────┬───────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
         ┌───────────────────────┐       ┌───────────────────────┐
         │ GROUNDED FORENSIC Q&A │       │ AUDITABLE PDF REPORTS │
         │   (Groq LLM / Rules)  │       │ (SHA-256 Digest Table)│
         └───────────────────────┘       └───────────────────────┘
```

---

## 4. Proposed Project Objectives

> These are original design objectives, not a report of verified current capabilities. Several are only partially implemented, and chain-of-custody or court-admissibility claims are outside this academic prototype's scope. See [PROJECT_STATUS.md](../PROJECT_STATUS.md) and [Solution_Requirements.md](../2.%20Requirement%20Analysis/Solution_Requirements.md) for current verification status.

### Objective 1: Unified Ingestion & Cryptographic Chain of Custody
Every uploaded file (image, audio, or video) is validated for MIME/magic-byte authenticity and hashed with SHA-256 before analysis. Hash digests are permanently embedded in session timelines and court-admissible PDF reports.

### Objective 2: Automated Multi-Tier Modality Analysis
- **Vision**: Object detection, zero-shot classification, and basic tampering/blur metrics.
- **Audio**: Automatic speech recognition (ASR), transcript segmenting, and acoustic fallback.
- **Video**: Keyframe extraction, optical motion analysis, and Intersection-over-Union (IoU) object tracking with persistent entity track IDs.

### Objective 3: Chronological Cross-Modal Fusion
Normalize all modality observations into a unified chronological timeline, enabling investigators to see correlated visual and acoustic events simultaneously.

### Objective 4: Offline-First Reliability & Architectural Grace
Ensure the entire platform operates fully in resource-constrained, offline environments through deterministic heuristic fallback tiers, eliminating hard dependencies on cloud infrastructure or external GPUs.

---
*Reference Implementation Files:*
- [config.py](../src/config.py)
- [services/image_service.py](../src/services/image_service.py)
- [services/audio_service.py](../src/services/audio_service.py)
- [services/video_service.py](../src/services/video_service.py)
- [services/fusion_service.py](../src/services/fusion_service.py)
