# CrimeVision AI — Academic Template Compliance

Reference structure: [AI-ML-and-GEN-AI-Track-Project-Template](https://github.com/Ravi-teja-777/AI-ML-and-GEN-AI-Track-Project-Template)

This repository uses the reference's eight phase folders for project deliverables. Unlike the PDF-only placeholders in the reference, the runnable implementation, tests, runtime requirements, and launch scripts are kept as source files under `src/`.

## Phase Mapping

| Reference phase | CrimeVision AI deliverables |
|---|---|
| `1. Brainstorming & Ideation/` | Empathy map, idea prioritization, problem statements |
| `2. Requirement Analysis/` | Requirements, technology stack, data-flow diagram, investigator journey |
| `3. Project Design Phase/` | Problem-solution fit, proposed solution, architecture |
| `4. Project Planning Phase/` | Project execution plan |
| `5. Project Development Phase/` | Feature inventory, code layout, implementation walkthrough; runnable code in [`src/`](src/) |
| `6.Project Testing/` | Test suite and performance report |
| `7.Project Documentation/` | Execution guide and system manual |
| `8.Project Demonstration/` | Demo plan and script, roadmap, stakeholder communication, team-role template |

## Runnable Application

The `src/` directory contains `app.py`, configuration, Flask routes, services, frontend templates and assets, tests, utilities, requirement files, and launch scripts. The root `README.md` documents setup and execution. Local case data, uploaded evidence, generated reports, virtual environments, and audit scratch files are not deliverables and are excluded by `.gitignore`.

## Evidence and Claims

- CrimeVision AI is an academic prototype, not a legally validated forensic system.
- Model availability is distinct from model accuracy. Results from synthetic inputs do not establish real-evidence accuracy.
- Heuristic image regions and frame-change observations are not semantic object detections.
- Cross-file media timestamps are not synchronized.
- Optional Groq requests require explicit user consent in the interface; chat sends only the current question and selected observation text, not prior local chat history or uploaded media bytes.
- The dashboard uses local assets and does not request remote fonts or send telemetry.
- `8.Project Demonstration/Team_Roles.md` leaves team and institution details unspecified. Add them only when accurate and required for submission; do not invent contributors or affiliations.

## Release Checklist

- [ ] Review `git status` and stage only individually reviewed source and documentation files.
- [ ] Confirm no `.env`, evidence, local case JSON, report, cache, virtual environment, or audit artifact is included.
- [ ] Review commit author metadata and the complete Git history before publication. Do not rewrite history without the repository owner's approval.
- [ ] Verify the intended GitHub repository and remote, then obtain explicit approval before pushing.
- [ ] Use synthetic or otherwise approved demo media only; do not publish private evidence or screenshots.
