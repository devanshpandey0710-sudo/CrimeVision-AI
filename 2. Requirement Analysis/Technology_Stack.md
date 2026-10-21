# Technology Stack: CrimeVision AI

## 1. Overview
CrimeVision AI is designed as a lightweight, local-first Python application. Dependencies are curated to deliver robust computer vision, automatic speech recognition, and report generation capabilities while remaining operable on standard CPU hardware.

---

## 2. Core Technology Stack Table

| Tier | Component / Technology | Exact Version / Dependency | Purpose in CrimeVision AI | Verification Status |
|---|---|---|---|---|
| **Backend Framework** | **Flask** | `Flask>=3.0.3` | Application server, Blueprint routing, JSON REST endpoints | **Import and app tests passed** ([app.py](../src/app.py)) |
| **Server Engine** | **Werkzeug** | `Werkzeug>=3.0.6` | Safe upload filenames and request routing | **Import verified** ([utils/file_utils.py](../src/utils/file_utils.py)) |
| **Deep Learning Runtime** | **PyTorch (CPU)** | Install separately when enabling models | Tensor computation for optional neural models | **Earlier project notes record cached RT-DETR and Whisper synthetic checks; not repeated in this release pass** |
| **Vision Models** | **Hugging Face Transformers** | `transformers>=4.44.2` (optional) | RT-DETR, BLIP, and Transformers CLIP model wrappers | **Current browser demo used heuristic fallback with zero semantic detections; BLIP/CLIP and accuracy unverified** |
| **Speech Recognition** | **OpenAI Whisper** | `openai-whisper>=20240930` (optional) | Local speech transcription when its model is available | **Earlier synthetic offline transcription is documented; real-recording accuracy unverified** |
| **Audio Resampling** | **SciPy** | `scipy>=1.11` (optional AI dependency) | Converts decoded audio to Whisper's 16 kHz input rate | **Verified with SciPy 1.18.1: synthetic 48 kHz stereo converted to 16 kHz mono** |
| **Computer Vision Engine** | **OpenCV** | `opencv-python>=4.10.0.84` | Video decoding, image metrics, and frame differencing | **Import verified; fallback paths covered by tests** |
| **Image Processing** | **Pillow (PIL)** | `Pillow>=10.4.0` | Image loading, conversion, and EXIF extraction | **Import verified; synthetic-image tests passed** |
| **Audio File I/O** | **SoundFile** | `soundfile>=0.12.1` | Audio decoding and acoustic measurements | **Import verified; synthetic-WAV tests passed** |
| **Report Generation** | **ReportLab** | `reportlab>=4.2.5` | Programmatic PDF report generation | **Import and PDF tests passed** ([services/report_service.py](../src/services/report_service.py)) |
| **LLM Inference Client** | **Groq SDK** | `groq>=0.11.0` (optional) | Optional cloud language-model requests | **Package import verified; no external API request made** |
| **Configuration** | **python-dotenv** | `python-dotenv>=1.0.1` | Environment-variable management | **Import verified** ([config.py](../src/config.py)) |
| **Testing Suite** | **pytest** | `pytest>=8.3.3` (test extra) | Automated test discovery and assertions | **146 passed (146 collected) offline; no model downloads or Groq requests** |
| **Frontend UI** | **HTML5 / Vanilla CSS / JS** | Modern browser standards | Responsive dark forensic UI, multi-track SVG timeline | **Loopback browser flow exercised with synthetic image** ([static/css/style.css](../src/static/css/style.css)) |

---

## 3. Component Categorization & Availability Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CRIMEVISION AI ARCHITECTURE TIERS                     │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ CORE RUNTIME                     │ OPTIONAL MODEL / SERVICE INTEGRATIONS   │
│ - Flask REST API & Web Server     │ - PyTorch + Transformers model runtime  │
│ - OpenCV / Pillow / SoundFile     │ - RT-DETR, BLIP, and CLIP weights       │
│ - SHA-256 file hashing            │ - Whisper weights for speech-to-text    │
│ - JSON case file persistence      │ - Groq API (key and network required)   │
│ - ReportLab PDF generation        │ - CUDA / GPU acceleration               │
│ - Heuristic fallback paths        │                                         │
│ - Interactive SVG timeline        │                                         │
└───────────────────────────────────┴─────────────────────────────────────────┘
```

### Notes on Hardware & Optional Integrations:
1. **CPU vs. GPU**: CPU is supported. PyTorch and model inference are optional and have not been performance-benchmarked on every machine. Install the CPU PyTorch build first when enabling neural models.
2. **Audio Decoding (SoundFile / FFmpeg)**: SoundFile-decodable files are supplied to Whisper as mono samples; SciPy handles sample-rate conversion. Formats SoundFile cannot decode may use Whisper's FFmpeg decoder. Without a usable decoder or Whisper model, the fallback reports acoustic measurements only and creates no transcript or speech timestamps. Broad format coverage remains unverified.
3. **Groq Cloud LLM**: Groq is optional. If no API key is provided, the platform uses its local rule-based chat fallback; no cloud request is made by default.

---
*Reference Implementation Files:*
- [requirements.txt](../src/requirements.txt)
- [config.py](../src/config.py)
- [app.py](../src/app.py)
