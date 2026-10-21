# Solution Architecture: CrimeVision AI

## 1. Architectural Philosophy
CrimeVision AI uses the Flask **Application Factory** pattern and singleton service instances for optional model runtimes. The model paths are designed for lazy loading; startup checks passed, but latency and memory use have not been benchmarked. Provenance fields describe the selected analysis path.

---

## 2. High-Level System Architecture Diagram

```mermaid
graph TB
    subgraph Presentation ["Presentation Layer (Client Browser)"]
        HTML["index.html (Semantic Dark UI)"]
        CSS["style.css (Design System Tokens)"]
        JS_Dash["dashboard.js (State & API Bindings)"]
        JS_Time["timeline.js (SVG Multi-Track Engine)"]
    end

    subgraph API_Layer ["API & Routing Layer (Flask 3.0)"]
        AppFactory["app.py (create_app Factory)"]
        R_Dash["dashboard_routes.py (GET /)"]
        R_Img["image_routes.py (/api/image/*)"]
        R_Aud["audio_routes.py (/api/audio/*)"]
        R_Vid["video_routes.py (/api/video/*)"]
        R_Evd["evidence_routes.py (/api/evidence/*)"]
        R_Chat["chat_routes.py (/api/chat/*)"]
        R_Rep["report_routes.py (/api/report/*)"]
    end

    subgraph Service_Layer ["Service Layer (Singleton Instances)"]
        S_Img["ImageService.get_instance()"]
        S_Aud["AudioService.get_instance()"]
        S_Vid["VideoService.get_instance()"]
        S_Fus["FusionService.get_instance()"]
        S_Int["IntelligenceService.get_instance()"]
        S_Chat["ChatService.get_instance()"]
        S_Rep["ReportService.get_instance()"]
    end

    subgraph Core_Utils ["Utilities & Schemas"]
        U_File["file_utils.py (Magic & SHA-256)"]
        U_Schema["evidence_schema.py (Validation)"]
        U_Time["timestamp_utils.py (Formatting)"]
    end

    subgraph Persistence ["Persistence Layer (Local File System)"]
        UploadsDir[("uploads/ (Raw Media & Frames)")]
        DataDir[("data/<case_id>.json (Case Store)")]
        ReportsDir[("reports/<case_id>_report.pdf")]
    end

    %% Wiring
    HTML --> JS_Dash
    JS_Dash --> JS_Time
    JS_Dash -->|REST Calls| API_Layer

    AppFactory --> R_Dash
    AppFactory --> R_Img
    AppFactory --> R_Aud
    AppFactory --> R_Vid
    AppFactory --> R_Evd
    AppFactory --> R_Chat
    AppFactory --> R_Rep

    R_Img --> S_Img
    R_Aud --> S_Aud
    R_Vid --> S_Vid
    R_Evd --> S_Fus
    R_Chat --> S_Chat
    R_Rep --> S_Rep

    S_Chat --> S_Int
    S_Int --> S_Fus
    S_Rep --> S_Fus

    S_Img --> S_Fus
    S_Aud --> S_Fus
    S_Vid --> S_Fus

    S_Img --> U_File
    S_Aud --> U_File
    S_Vid --> U_File
    S_Fus --> U_Schema

    U_File --> UploadsDir
    S_Fus --> DataDir
    S_Rep --> ReportsDir
```

---

## 3. Structural Breakdown

### 3.1 Application Factory ([app.py](../src/app.py))
- Instantiates Flask with explicit configuration from `config.py`.
- Registers seven dedicated Blueprints (`dashboard`, `image`, `audio`, `video`, `evidence`, `chat`, `report`).
- Configures error handlers (`400`, `404`, `413`, `500`) returning consistent JSON responses.
- Provides `/api/health` and `/api/models/status` endpoints returning system and optional-service status without exposing API keys.

### 3.2 Blueprint Organization ([routes/](../src/routes/))
Each route module is strictly isolated to its evidentiary modality:
- `image_routes.py`: File upload, validation, and invocation of `image_service`.
- `audio_routes.py`: Audio intake, Whisper transcription, and acoustic analysis.
- `video_routes.py`: Video intake, keyframe extraction, and IoU tracking.
- `evidence_routes.py`: Timeline retrieval, case listing, and case deletion. The DELETE route is unauthenticated and should only be used in a trusted local session; this audit did not call it.
- `chat_routes.py`: Natural language Q&A scoped to case observations.
- `report_routes.py`: Generation and download of academic prototype PDF documents.

### 3.3 Singleton Service Organization ([services/](../src/services/))
- Optional runtimes (RT-DETR, Whisper, CLIP, and Groq clients) are managed through service instances.
- **Lazy Loading**: Model weights may load on first use and may require network access. No weight-loading path was run in the safe audit suite.

### 3.4 Shared Utilities ([utils/](../src/utils/))
- `file_utils.py`: Enforces upload-size and extension checks, validates supported signatures, and computes SHA-256 digests for later comparison.
- `evidence_schema.py`: Defines `TypedDict` observation shapes, a dictionary factory, and basic required-field/confidence validation; it does not validate the truth of evidence.
- `timestamp_utils.py`: Formats media-relative numeric offsets for display. Times from separate files are not synchronized.

---
*Reference Implementation Files:*
- [app.py](../src/app.py)
- [config.py](../src/config.py)
- [routes/__init__.py](../src/routes/__init__.py)
- [services/__init__.py](../src/services/__init__.py)
