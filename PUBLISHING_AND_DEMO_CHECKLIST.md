# Final Publishing and Demo Checklist

## Before the first GitHub push
- Confirm this is the `CrimeVision-AI-clean-release` folder, not the original project.
- Review `git status --short`; only stage reviewed source/documentation files.
- Verify `.env` is absent; keep `.env.example` with placeholders.
- Keep real evidence, local case JSON, uploads, reports, model weights, virtual environments, and caches out of Git.
- Choose a repository license only if the relevant rights holder authorizes it. No license is included by default.
- Create an empty GitHub repository, then set its remote locally. Never paste an access token into chat or a source file.
- Review the staged diff before committing. Do not use `git add .` blindly.

## Demo recording (real app recording only)
1. Use synthetic media and a fresh synthetic case ID. Never use real forensic evidence.
2. Close personal tabs, notifications, password managers, and unrelated windows.
3. Start the app locally and confirm it listens on `127.0.0.1` only.
4. Record: dashboard/health → synthetic image upload → show actual inference source and detection count → timeline → decline external chat processing and show local response → generate and open PDF report.
5. If the image path reports heuristic fallback, say so clearly; do not call heuristic regions object detections.
6. Do not claim a live Groq/model workflow unless it was genuinely configured and run.
7. Review the entire recording for private paths, usernames, tokens, case data, and accidental notifications before sharing.

## Known verification limit
A prior run recorded 146 passing tests, but the latest packaging audit could not reproduce it because pytest was unavailable in that environment. Do not describe the latest audit as a fresh passing test run. The demo should show only behavior actually observed.
