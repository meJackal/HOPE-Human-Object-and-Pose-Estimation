# Setup & Usage (Local Development)

This document describes how to set up the project for development or to run locally (non-Pi specific).

Prerequisites

- Python 3.10+
- Git (optional)
- Camera (USB webcam) or recorded video for testing

Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # use .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Run the server (development)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open the UI

- Visit `http://localhost:8000` or `http://<host-ip>:8000` from another machine on the network.

API overview

- `GET /` — Initialization page
- `GET /detection` — Detection UI
- `GET /status` — Server status
- `POST /start` and `POST /stop` — Control detection
- `WebSocket /ws` — Live pose stream

Logs & Diagnostics

- Detection events are saved to `logs/detections.json` by default.
- For server runtime issues, review console output where `uvicorn` runs or check the systemd logs if running as a service.

Common tasks

- Re-download model (delete `backend/yolov8n-pose.pt` and restart server).
- Change camera device index in `backend/main.py` if the default `0` is not correct.

Security

- This project does not implement authentication by default. Restrict network access or add reverse-proxy authentication for public deployments.

Project structure

```
Human-Detection/
├── README.md
├── SETUP.md
├── RASPBERRY_PI_SETUP.md
├── backend/
├── frontend/
└── logs/
```
