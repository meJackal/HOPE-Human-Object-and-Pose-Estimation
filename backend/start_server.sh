#!/bin/bash

PROJECT_DIR="/home/julius/Documents/Human-Detection"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
LOG_FILE="$PROJECT_DIR/logs/startup.log"

mkdir -p "$PROJECT_DIR/logs"

echo "[$(date)] STARTING YOLOv8 SYSTEM (USING .venv)" >> "$LOG_FILE"

cd "$BACKEND_DIR" || {
    echo "ERROR: Cannot access backend directory" >> "$LOG_FILE"
    exit 1
}

# HARD CHECK
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: .venv Python not found at $VENV_PYTHON" >> "$LOG_FILE"
    exit 1
fi

exec "$VENV_PYTHON" -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    >> "$LOG_FILE" 2>&1