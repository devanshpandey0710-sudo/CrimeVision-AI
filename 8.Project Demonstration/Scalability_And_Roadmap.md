# Scalability & Future Roadmap: CrimeVision AI

## 1. Overview
CrimeVision AI is an academic single-workstation prototype. Its Flask services separate some modality and reporting responsibilities, but it is not load-tested, multi-user, or validated for operational forensic work. This document records constraints and possible future enhancements, not current capabilities.

---

## 2. Current Architectural Constraints

| Component | Current State | Operational Constraint |
|---|---|---|
| **Data Persistence** | Atomic JSON files (`data/<case_id>.json`) | High read/write speed for single cases; not optimized for concurrent multi-user writes. |
| **Media Storage** | Local directory (`uploads/`) | Bound by the host workstation's local storage capacity. |
| **Compute Engine** | Multi-threaded CPU execution | Video frame decoding and neural inference scale with CPU core count. |
| **Video Ingress** | File container uploads (`.mp4`, `.avi`, `.mov`) | Offline / recorded media only; no live RTSP camera stream decoding. |
| **LLM Inference** | Groq Cloud API with local rule fallback | Cloud API requires outbound internet access (mitigated by offline rule fallback). |

---

## 3. Future Scalability Roadmap

```
                    CRIMEVISION AI ARCHITECTURAL EVOLUTION

[ CURRENT WORKSTATION ARCHITECTURE ]
  Local Flask Server + JSON Store + Local CPU Inference + Heuristic Tiers
                                │
                                ▼
[ PHASE I: ENTERPRISE DATA STORE ]
  Migrate JSON store to PostgreSQL + TimescaleDB for temporal indexing
  Migrate local uploads/ to S3-compatible object storage (MinIO)
                                │
                                ▼
[ PHASE II: DISTRIBUTED INFERENCE PIPELINES ]
  Decouple Video/Audio analysis into Celery / Redis background worker queues
  Optional GPU acceleration nodes (NVIDIA Triton Inference Server)
                                │
                                ▼
[ PHASE III: LIVE SENSOR INGESTION & EDGE DEPLOYMENT ]
  Real-time RTSP surveillance video decoding via OpenCV / GStreamer
  Local quantized GGUF LLMs (via llama.cpp) for air-gapped forensic facilities
```

### Roadmap Milestone 1: Relational Persistence with Temporal Indexing
- **Target**: Replace flat-file JSON persistence with **PostgreSQL** featuring relational integrity constraints and a **TimescaleDB** extension.
- **Benefit**: Enables sub-millisecond timeline range queries across thousands of concurrent cases and multi-analyst collaboration.

### Roadmap Milestone 2: Asynchronous Task Workers (Celery & Redis)
- **Target**: Offload long-running video and audio transcription jobs to asynchronous worker pools using Celery and Redis.
- **Benefit**: Allows the web UI to remain immediately responsive while multi-hour surveillance videos process in the background with progress webhooks.

### Roadmap Milestone 3: Live CCTV Streaming & Edge Deployment
- **Target**: Integrate GStreamer or RTSP camera ingress to sample live video feeds directly from municipal camera networks.
- **Benefit**: Enables proactive crime scene perimeter monitoring and live entity tracking during ongoing emergency responses.

### Roadmap Milestone 4: Fully Air-Gapped Local LLM (Quantized GGUF)
- **Target**: Embed local quantized LLaMA-3 models (e.g., 8-bit quantized GGUF via `llama.cpp` or Ollama).
- **Benefit**: Achieves high-level natural language synthesis in completely air-gapped, high-security law enforcement environments without external API calls.

---
*Reference Implementation Files:*
- [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md)
- [PROJECT_STATUS.md](../PROJECT_STATUS.md)
- [services/fusion_service.py](../src/services/fusion_service.py)
