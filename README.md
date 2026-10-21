# CrimeVision AI – Intelligent Multimodal Forensic Analysis Platform

> Academic project prototype.

CrimeVision AI is an academic Flask prototype for image, video, and audio workflows.
It combines available model output and clearly labelled heuristic observations in a
case timeline, provides local evidence-grounded chat, and generates downloadable PDF
reports. Optional models may be unavailable; heuristic output is not object detection.

---

## ⚠ Disclaimer

This platform is an **academic demonstration tool**. Reports and analyses produced by
CrimeVision AI are **not legally validated forensic evidence** and must not be used
as the sole basis for legal or official decisions. AI-generated interpretations are
clearly labelled as such throughout the application.

---

## 📁 Academic Project Deliverables (8-Phase Track)

This repository adheres to the standardized academic curriculum track deliverables:

1. **[Phase 1: Brainstorming & Ideation](1.%20Brainstorming%20%26%20Ideation/)**
   - [Idea Prioritization](1.%20Brainstorming%20%26%20Ideation/Idea_Prioritization.md) | [Problem Statements](1.%20Brainstorming%20%26%20Ideation/Problem_Statements.md) | [Empathy Map](1.%20Brainstorming%20%26%20Ideation/Empathy_Map.md)
2. **[Phase 2: Requirement Analysis](2.%20Requirement%20Analysis/)**
   - [Investigator Journey Map](2.%20Requirement%20Analysis/Investigator_Journey_Map.md) | [Data Flow Diagram](2.%20Requirement%20Analysis/Data_Flow_Diagram.md) | [Solution Requirements](2.%20Requirement%20Analysis/Solution_Requirements.md) | [Technology Stack](2.%20Requirement%20Analysis/Technology_Stack.md)
3. **[Phase 3: Project Design Phase](3.%20Project%20Design%20Phase/)**
   - [Problem-Solution Fit](3.%20Project%20Design%20Phase/Problem_Solution_Fit.md) | [Proposed Solution](3.%20Project%20Design%20Phase/Proposed_Solution.md) | [Solution Architecture](3.%20Project%20Design%20Phase/Solution_Architecture.md)
4. **[Phase 4: Project Planning Phase](4.%20Project%20Planning%20Phase/)**
   - [Project Execution Plan](4.%20Project%20Planning%20Phase/Project_Execution_Plan.md)
5. **[Phase 5: Project Development Phase](5.%20Project%20Development%20Phase/)**
   - Runnable source code: [`src/`](src/) | [Code Layout & Design Patterns](5.%20Project%20Development%20Phase/Code_Layout_And_Design_Patterns.md) | [Implementation Walkthrough](5.%20Project%20Development%20Phase/Implementation_Walkthrough.md) | [Feature Inventory](5.%20Project%20Development%20Phase/Feature_Inventory.md)
6. **[Phase 6: Project Testing](6.Project%20Testing/)**
   - [Test Suite & Performance Report](6.Project%20Testing/Test_Suite_And_Performance_Report.md)
7. **[Phase 7: Project Documentation](7.Project%20Documentation/)**
   - [Execution Guide](7.Project%20Documentation/Execution_Guide.md) | [System Manual](7.Project%20Documentation/System_Manual.md)
8. **[Phase 8: Project Demonstration](8.Project%20Demonstration/)**
   - [Stakeholder Communication](8.Project%20Demonstration/Stakeholder_Communication.md) | [Feature Demonstration Script](8.Project%20Demonstration/Feature_Demonstration_Script.md) | [Demo Plan](8.Project%20Demonstration/Demo_Plan.md) | [Scalability & Roadmap](8.Project%20Demonstration/Scalability_And_Roadmap.md) | [Team Roles](8.Project%20Demonstration/Team_Roles.md)

See [TEMPLATE_COMPLIANCE.md](TEMPLATE_COMPLIANCE.md) for the phase mapping and current release checks. The eight folders contain Markdown deliverables; the runnable application and tests are in `src/`, not in PDF attachments.
---


## Features

| Module | Description | Status |
|--------|-------------|--------|
| **Image Analysis** | Optional RT-DETR/BLIP/CLIP paths and clearly labelled heuristic fallbacks | The browser demo used OpenCV heuristic regions, with zero semantic detections; prior synthetic model checks do not establish accuracy |
| **Audio Analysis** | Optional local Whisper transcription and acoustic measurements | A previous offline synthetic speech check transcribed; real-recording accuracy and broad format support are unverified |
| **Video Analysis** | Sampled keyframes, frame-change observations, optional detector/tracker | A previous synthetic RT-DETR check had zero detections; real-video accuracy is unverified |
| **Fusion Timeline** | Shared observation schema, per-source media-relative timestamps, case JSON | Partial; separate files are not synchronized |
| **AI Chat** | Local keyword lookup; optional Groq after explicit consent | Browser demo confirmed local-only response after consent was declined; live Groq behavior unverified |
| **PDF Reports** | ReportLab-generated downloadable academic prototype report | Implemented path; generated content requires review |
| **Dashboard** | Flask HTML/CSS/JavaScript dashboard and REST API wiring | Loopback browser workflow exercised upload, analysis, timeline, local chat, and report generation; no screenshots saved |
| **Health / API** | REST API with health endpoint | Flask tests passed; live loopback health endpoint returned HTTP 200 |

---

## Technology Stack

- **Backend:** Python (project environment verified with 3.14.8), Flask, Flask-CORS
- **Vision:** OpenCV and Pillow are core; PyTorch and Hugging Face Transformers are optional model integrations. The code uses Transformers' CLIP implementation.
- **Audio:** SoundFile is core; OpenAI Whisper is an optional local transcription model.
- **LLM:** Groq SDK is optional; local paths work without an account or key. Transcript/evidence text is sent only after an explicit per-action browser confirmation.
- **PDF:** ReportLab
- **Frontend:** HTML5, CSS3, Vanilla JS (no framework required)
- **Testing:** pytest

---

## Installation (Windows PowerShell)

### Prerequisites

- Python 3.11–3.14 (the current local run used Python 3.14.8; other versions have not all been tested)
- pip 23+
- Git (optional)

### Step 1: Open a terminal in the project directory

Open your preferred terminal (PowerShell, Command Prompt, or bash) and navigate to the project root directory:

```bash
cd "<PROJECT_ROOT>"
```

*(Or right-click the project folder and select **Open in Terminal**)*


### Step 2: Check Python version

```powershell
python --version
# Check that Python 3.11 or newer in the documented range is active
```

### Step 3: Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
# Prompt should now show (venv)
```

If you get a script execution error, run this once:
```powershell
# You can skip activation and run tools through the virtual environment directly:
.\venv\Scripts\python.exe -m pip install -r src\requirements.txt
```

### Step 4: Upgrade pip and install core dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r src\requirements.txt
```

### Step 5: Install optional AI model dependencies (only if needed)

```powershell
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r src\requirements-ai.txt
```

This optional step enables local neural-model integrations. Model weights are local-only by default: if a checkpoint is already cached, the app can use it; otherwise it reports the model unavailable and uses the clearly labeled fallback. It will not fetch weights on first use. Only set `ALLOW_MODEL_DOWNLOADS=1` after you have explicitly approved a model download; some weights are large. You can leave Groq unconfigured and keep its optional features disabled.

### Step 6: Install test tools (optional)

```powershell
python -m pip install -r src\requirements-test.txt
```

### Step 7: Configure environment

```powershell
Copy-Item src\.env.example src\.env
notepad src\.env
```

`GROQ_API_KEY` is optional. Leave it unset to use local rule-based chat. If you choose Groq, store its key only in the ignored `.env` file; do not paste it into source code or share it in chat.

### Step 8: Verify imports without loading models

```powershell
python -c "import flask, flask_cors, cv2, PIL, numpy, soundfile, reportlab; print('Core imports OK')"
```

This checks installed packages only; it does not load or download model weights. No separate OpenAI CLIP installation is used by the current code.

---

## Running the Application

### Option A: Quick Launch Script (Recommended)

**PowerShell (from the repository root):**
```powershell
.\src\launch.ps1
```

**Windows Batch (or double-click from File Explorer):**
```cmd
src\launch.bat
```

Both launch scripts use the repository-root `venv`, keep runtime files under `src\data`, `src\uploads`, and `src\reports`, initialize `src\.env` from its example if missing, and bind the Flask server to **http://127.0.0.1:5000**.

### Option B: Manual Launch

```powershell
Set-Location src
..\venv\Scripts\python.exe app.py
```

Open your browser: **http://127.0.0.1:5000**


---

## Running Tests

```powershell
Set-Location src
python -m pytest tests/ -v
```

To run with coverage:

```powershell
Set-Location src
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

Most recent local verification: **146 tests passed** on Python 3.14.8 with pytest 8.3.3, model downloads disabled, `.env` loading disabled, and output paths isolated from local case data. This functional suite result is not a model-accuracy or performance claim.

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Dashboard UI |
| GET | `/api/health` | System health and config |
| GET | `/api/cases` | List all cases |
| POST | `/api/image/analyse` | Upload and analyse an image |
| POST | `/api/audio/transcribe` | Upload and transcribe audio |
| POST | `/api/video/analyse` | Upload and analyse a video |
| GET | `/api/image/annotated/<evidence_id>` | View a generated annotated image, when real detections were produced |
| GET | `/api/video/keyframes/<evidence_id>/<filename>` | View a generated sampled keyframe |
| POST | `/api/audio/events` | Optional candidate transcript-event extraction; confirmation required in dashboard |
| POST | `/api/video/classify` | Optional tentative classification of analyzed video observations; confirmation required in dashboard |
| GET | `/api/evidence/timeline/<case_id>` | Unified evidence timeline |
| DELETE | `/api/evidence/case/<case_id>` | Delete a case |
| POST | `/api/chat/ask` | Evidence-grounded chat; JSON `allow_external` defaults to `false` |
| GET | `/api/chat/history/<case_id>` | Conversation history |
| DELETE | `/api/chat/history/<case_id>` | Clear history |
| POST | `/api/report/generate` | Generate PDF report |
| GET | `/api/report/download/<case_id>` | Download generated PDF |

---

## Project Structure

```
CrimeVision AI/
├── .gitignore
├── PROJECT_STATUS.md
├── DEVELOPMENT_LOG.md
├── README.md
├── TEMPLATE_COMPLIANCE.md
├── 1. Brainstorming & Ideation/
├── 2. Requirement Analysis/
├── 3. Project Design Phase/
├── 4. Project Planning Phase/
├── 5. Project Development Phase/
├── 6.Project Testing/
├── 7.Project Documentation/
├── 8.Project Demonstration/
└── src/                    # Runnable application, tests, launchers, requirements
    ├── app.py
    ├── config.py
    ├── requirements*.txt
    ├── routes/
    ├── services/
    ├── utils/
    ├── templates/
    ├── static/
    ├── tests/
    ├── data/               # Local case JSON (ignored except .gitkeep)
    ├── uploads/            # Local evidence (ignored except .gitkeep)
    └── reports/            # Generated PDFs (ignored except .gitkeep)
```

---

## Approximate Model Storage Requirements

| Model | Size | Notes |
|-------|------|-------|
| Whisper `base` | ~74 MB | CPU compatible |
| RT-DETR `r18vd` | ~66 MB | CPU compatible |
| BLIP `base` | ~446 MB | CPU compatible |
| CLIP `ViT-B/32` | ~338 MB | CPU compatible |

Model weights are local-only by default. Missing checkpoints are reported as unavailable and the app uses its labelled fallback; model analysis will not fetch weights automatically. Locally cached weights may be used. Do not enable `ALLOW_MODEL_DOWNLOADS=1` unless you have explicitly approved a download; files can be large.

---

## Troubleshooting

**PowerShell execution policy error**
```powershell
# Skip activation; run the project's Python directly:
Set-Location src
..\venv\Scripts\python.exe app.py
```

**`torch` import fails**
> Reinstall: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`

**Whisper audio decoding**
> SoundFile-decodable files are passed to Whisper as samples; SciPy in the optional AI requirements handles sample-rate conversion. Formats SoundFile cannot decode may use FFmpeg. Install ffmpeg from https://ffmpeg.org/download.html and add it to PATH for those formats.

**Optional Groq feature is unavailable**
> The local lookup remains available. To use the optional service, configure your own key privately in `.env`; never paste it into chat or commit it. Confirm each transmission in the browser.

**App crashes on video upload**
> Ensure OpenCV can read the codec. Install `opencv-python` (not `opencv-python-headless`).

---

## Known Limitations

- Synthetic offline checks and this release test run do not establish model accuracy. Treat heuristic image regions and frame changes as candidates/observations, not semantic object detections or forensic conclusions.
- Speaker diarization is disabled by default (requires `pyannote.audio` with Hugging Face token).
- RT-DETR is trained on COCO classes; it will not detect specialized forensic items
  unless a domain-specific model is fine-tuned.
- Video processing is limited by upload size, maximum sampled frames, and `VIDEO_MAX_FRAME_PIXELS`; codec support depends on the installed OpenCV build.
- BLIP image captioning requires ~1–3 GB RAM on CPU.

## Privacy and Security Notes

- The development server binds to `127.0.0.1` by default and has no authentication; do not expose it to a network.
- Dashboard assets are local; the page does not request remote fonts. The app does not send telemetry.
- Model downloads are disabled by default. Keep `ALLOW_MODEL_DOWNLOADS=0` unless a download is explicitly approved.
- Optional Groq actions require explicit consent. Chat sends the current question and selected observation text only; earlier local chat history and uploaded media bytes are not included in the chat request. Other optional analysis actions can send their displayed transcript/observation text after confirmation.
- Case JSON, uploaded evidence, and generated reports persist locally in `src/data/`, `src/uploads/`, and `src/reports/`. These paths are ignored by Git, but Git ignore rules do not exclude them from a manually created whole-folder archive.

---

## Git Setup

```powershell
git status --short
```

Review the status before choosing files. After you explicitly decide to stage files, use `git add <specific-path>` for each reviewed source or document. Never use `git add .` or `git add -A` in this project. Do not stage, commit, or push without the project owner's approval.

The `.gitignore` prevents committing:
- `.env` files (secrets)
- `src/uploads/` (forensic evidence)
- `src/data/` (case data)
- `src/reports/` (generated PDFs)
- `venv/` (virtual environment)
- Model weight files (`.bin`, `.safetensors`, `.pt`)

Do not distribute a zip of the entire working folder: ignored local evidence, case data, reports, virtual environments, and audit scratch folders may still be present there. Publish only reviewed Git files after history and identity review.

---

## Academic Submission Notes

- This project demonstrates integration of multiple AI modalities in a single platform.
- Suitable for IT project presentations, Skill Wallet submissions, and academic reports.
- Screenshots recommended: dashboard home, image analysis result, timeline view, AI chat.
