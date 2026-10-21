# Code Layout & Design Patterns: CrimeVision AI

## 1. Repository Directory Structure
CrimeVision AI separates the academic deliverables at the repository root from the runnable application under `src/`. Within `src/`, Flask routes, services, utilities, templates, static assets, and tests are kept in separate directories.

```text
├── 1. Brainstorming & Ideation/
├── 2. Requirement Analysis/
├── 3. Project Design Phase/
├── 4. Project Planning Phase/
├── 5. Project Development Phase/
├── 6.Project Testing/
├── 7.Project Documentation/
├── 8.Project Demonstration/
├── README.md
├── TEMPLATE_COMPLIANCE.md
└── src/
    ├── app.py                  # Flask application factory and local entry point
    ├── config.py               # Environment-based configuration
    ├── routes/                 # Flask API blueprints
    ├── services/               # Image/audio/video/fusion/chat/report logic
    ├── utils/                  # Validation, schema, and file helpers
    ├── templates/              # Dashboard HTML
    ├── static/                 # CSS and JavaScript
    ├── tests/                  # pytest suite
    ├── requirements*.txt       # Core, optional AI, and test dependencies
    ├── launch.bat / launch.ps1 # Local Windows launchers
    ├── data/                   # Local case data (ignored except .gitkeep)
    ├── uploads/                # Local evidence (ignored except .gitkeep)
    └── reports/                # Generated PDFs (ignored except .gitkeep)
```

---

## 2. Core Architectural Design Patterns

### Pattern 1: Application Factory Pattern ([app.py](../src/app.py))
- Rather than a global Flask instance, `create_app(test_config=None)` instantiates and configures the app instance.
- Facilitates automated testing by allowing tests to pass in mock configurations and temporary directories without modifying application state.

### Pattern 2: Blueprint-per-Modality Pattern ([routes/](../src/routes/))
- Routes are cleanly partitioned into 7 modular Blueprints.
- Each route file is responsible solely for HTTP request decoding, schema validation, invoking the appropriate service, and formatting JSON responses.

### Pattern 3: Singleton Service Pattern ([services/](../src/services/))
- Heavy services implement the `get_instance()` class method.
- Ensures AI model weights and tokenizer pipelines are initialized once and shared across requests, preventing multi-gigabyte memory leaks.
- Supports dependency injection in unit tests by replacing singleton instances with lightweight test doubles.

### Pattern 4: Strategy / Fallback Pattern
- Every AI modality encapsulates a tiered execution strategy:
  1. Primary Strategy: Deep learning inference (PyTorch, Transformers, Whisper).
  2. Fallback Strategy: Deterministic heuristics (Laplacian edge detection, energy envelope profiling, frame differencing).
- Automatically protects the system against crashes when models or GPUs are unavailable.

---

## 3. Code Maintainability & Clean Code Standards
- **Explicit Type Hints**: All function signatures use Python 3.10+ type annotations (e.g. `Path`, `dict[str, Any]`, `list[Observation]`).
- **Cryptographic Grounding**: SHA-256 computation is centralized in [utils/file_utils.py](../src/utils/file_utils.py) and called consistently across all ingestion pipelines.
- **Strict Error Handling**: Handled exceptions log contextual information while returning user-friendly JSON payloads (`{"error": "...", "status": 400}`).

---
*Reference Implementation Files:*
- [app.py](../src/app.py)
- [services/image_service.py](../src/services/image_service.py)
- [utils/evidence_schema.py](../src/utils/evidence_schema.py)
