# Empathy Map & User Personas: CrimeVision AI

> **Notice Regarding Methodology**: The personas and empathy maps presented below are proposed theoretical archetypes based on forensic investigation domain workflows and law enforcement standard operating procedures. They do not represent empirical interviews or survey results with active police personnel.

---

## 1. Proposed User Persona: Forensic Digital Evidence Analyst

### Profile
- **Role**: Detective / Digital Forensic Analyst (Law Enforcement / Private Investigation)
- **Primary Objective**: Process seized digital media quickly, extract verified factual observations, establish chronological timelines, and prepare court-admissible reports.
- **Environment**: Secure local forensic workstation, frequently air-gapped or restricted from public internet access.

### Empathy Map

```
┌───────────────────────────────────────────────────────────────┐
│                           SAYS                                │
│ "I need to know the exact timestamp this suspect entered the  │
│ alley, and I need a verifiable hash for this video."          │
│ "I can't send this footage to a third-party cloud API."       │
├───────────────────────────────┬───────────────────────────────┤
│            THINKS             │             DOES              │
│ - "Is this evidence untampered?"│ - Samples video frames manually │
│ - "Will defense counsel       │ - Transcribes 911 audio tapes  │
│   challenge my AI model's     │ - Compiles Excel spreadsheets   │
│   provenance in court?"       │   to align audio and video     │
│ - "My workstation has no GPU."│ - Verifies SHA-256 hashes     │
├───────────────────────────────┴───────────────────────────────┤
│                            FEELS                              │
│ - Overwhelmed by backlogs of multi-hour surveillance footage. │
│ - Anxious about missing subtle background details.           │
│ - Pressured by strict court filing deadlines.                 │
└───────────────────────────────────────────────────────────────┘
```

### Key Pain Points
1. **Multi-Format Ingestion**: Switching between video players, audio spectrogram viewers, and EXIF readers.
2. **Provenance Doubts**: "Black box" AI predictions that fail to state their confidence or method.
3. **Data Privacy**: Legal prohibitions against uploading unredacted evidentiary recordings to public cloud services.

### Desired Gains
1. A single local interface where photos, audio, and videos are ingested into one synchronized timeline.
2. Complete transparency: clearly labeled provenance tags (`deep_learning` vs `heuristic_fallback`).
3. Automated court-ready PDF export showing full SHA-256 cryptographic hashes for every piece of evidence.

---

## 2. Proposed User Persona: Lead Investigating Officer

### Profile
- **Role**: Senior Detective / Case Officer
- **Primary Objective**: Synthesize disparate clues, understand suspect actions, query case facts, and make informed operational decisions.
- **Technical Literacy**: Intermediate; focuses on investigative facts rather than machine learning architectures.

### Empathy Map
- **Says**: "Give me a high-level summary of all vehicle detections between 02:00 AM and 03:00 AM."
- **Thinks**: "I need reliable answers grounded only in verified case files, not hallucinations."
- **Does**: Reviews evidence summaries, asks questions about witness statements, coordinates team leads.
- **Feels**: Needs high confidence in facts before issuing search warrants or interrogating persons of interest.

---
*Reference Implementation Files:*
- [templates/index.html](../src/templates/index.html)
- [services/chat_service.py](../src/services/chat_service.py)
- [services/report_service.py](../src/services/report_service.py)
