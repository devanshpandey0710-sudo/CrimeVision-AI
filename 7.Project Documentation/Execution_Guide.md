# Execution Guide: CrimeVision AI

## 1. Overview
This execution guide provides setup, dependency installation, configuration, and launch instructions for the CrimeVision AI platform. It contains no personal usernames, machine-specific paths, or live API credentials.

---

## 2. Prerequisites
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS (12+).
- **Python**: Python 3.11–3.14 is the documented range. The current project virtual environment reports Python 3.14.8; this audit did not test every version in the range.
- **Package Manager**: `pip` (version 23.0+).
- **FFmpeg (Optional)**: SoundFile-decodable files use the in-process Whisper input path; formats SoundFile cannot decode may require FFmpeg. SciPy in the optional AI dependencies is used for sample-rate conversion.

---

## 3. Step-by-Step Installation

### Step 1: Open Terminal in Project Root
Navigate to the project root directory:
```bash
cd "path/to/CrimeVision AI – Intelligent Multimodal Forensic Analysis Platform"
```

### Step 2: Initialize Virtual Environment
Create and activate an isolated Python virtual environment:
```powershell
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS (bash)
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Core Dependencies
Install the application dependencies from `src/requirements.txt`:
```bash
python -m pip install --upgrade pip
python -m pip install -r src\requirements.txt
```

### Step 4: Optional AI Integrations
The app can run its non-neural fallback paths without downloading model weights. To enable local neural models, install CPU PyTorch and the optional model packages:
```powershell
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r src\requirements-ai.txt
```
Model weights are local-only by default. Cached weights may be used; missing weights result in a clear unavailable/fallback path, without an internet download. `ALLOW_MODEL_DOWNLOADS` defaults to `0`. Do not set it to `1` unless you explicitly approve downloading the selected model weights. Groq is optional and requires a user-provided key only if cloud chat is desired.

### Step 5: Optional Test Dependencies
```powershell
python -m pip install -r src\requirements-test.txt
Set-Location src
python -m pytest tests/ -v
```

---

## 4. Environment Configuration (`.env`)

CrimeVision AI includes a clean configuration template named [.env.example](../src/.env.example).

1. Copy the example template inside `src/` to create your local `src/.env`:
   ```powershell
   # Windows
   Copy-Item src\.env.example src\.env

   # Linux / macOS
   cp src/.env.example src/.env
   ```
2. Open `src/.env` in a text editor and adjust values if needed:
   - `SECRET_KEY`: Optional. Use a long random value for a stable key across restarts. If blank or a known placeholder, the app generates a random per-run key.
   - `GROQ_API_KEY`: Optional. Leave unset to use local rule-based chat; a Groq account is not required.
   - `ALLOW_MODEL_DOWNLOADS`: Defaults to `0`, so missing neural model files are not downloaded automatically. Keep it at `0` to stay offline; only enable downloads after you approve them.
   - `CORS_ORIGINS`: Optional comma-separated origin allowlist. By default, only localhost origins on the configured port are allowed.
   - `PORT`: Default is `5000`.

---

## 5. Starting the Platform

### Option A: Automated Launchers (Windows)
From the repository root, use a launcher in `src/`. The launchers use the virtual environment at the repository root:
```powershell
.\src\launch.ps1
# or
src\launch.bat
```

`src\launch.ps1` accepts `-Port`, `-Debug`, and `-NoBrowser`. `src\desktop_launcher.bat` is an optional Windows helper that uses the current user's Desktop location dynamically.

### Option B: Manual Terminal Launch (Cross-Platform)
Run the application from `src/`, with the repository-root virtual environment active:
```bash
cd src
python app.py
```
```powershell
Set-Location src
..\venv\Scripts\python.exe app.py
```
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 6. Troubleshooting Common Issues

| Issue / Error | Probable Cause | Recommended Resolution |
|---|---|---|
| **Port 5000 in use** | Another application is bound to 5000. | Change `PORT=5050` in `.env` and restart. |
| **`ffmpeg` not recognized** | SoundFile could not decode the audio file for the Whisper path. | Install FFmpeg from [https://ffmpeg.org](https://ffmpeg.org) and add it to system PATH. SoundFile-decodable files use the in-process path; other formats may need FFmpeg. |
| **"LLM unavailable (offline mode)"** | `GROQ_API_KEY` is missing or Groq cannot be reached. | Expected behavior in offline mode; local rule-based chat remains available. Groq is optional. |
| **Memory pressure during video processing** | Video is excessively long or high resolution. | Lower `VIDEO_FRAME_INTERVAL_SEC=4` in `.env` to sample fewer keyframes. |
| **`python -m venv` reports an `ensurepip` error** | Python could create the environment folder but could not bootstrap its bundled pip. | Repair or reinstall Python with its standard-library `ensurepip` component. If an existing Python environment has pip 23+, it can target the new interpreter with `python -m pip --python .\new-venv\Scripts\python.exe install -r src\requirements.txt`. |

---
*Reference Implementation Files:*
- [.env.example](../src/.env.example)
- [requirements.txt](../src/requirements.txt)
- [requirements-ai.txt](../src/requirements-ai.txt)
- [requirements-test.txt](../src/requirements-test.txt)
- [desktop_launcher.bat](../src/desktop_launcher.bat)
- [launch.bat](../src/launch.bat)
- [launch.ps1](../src/launch.ps1)
