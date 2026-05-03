#!/bin/bash

echo "======================================"
echo "YOLOv8 Raspberry Pi Setup"
echo "======================================"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project: $PROJECT_DIR"
echo ""

# ===== 1. Make scripts executable =====
echo "[1/4] Setting permissions..."
chmod +x "$SCRIPT_DIR/start_server.sh"
echo "✓ start_server.sh ready"
echo ""

# ===== 2. Fix service file path =====
echo "[2/4] Fixing systemd service file..."

sed -i "s|/home/julius/Documents/Human-Detection|$PROJECT_DIR|g" \
    "$SCRIPT_DIR/yolov8-detection.service"

echo "✓ service file updated"
echo ""

# ===== 3. Create virtual environment =====
echo "[3/4] Creating venv..."

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "✓ venv created"
fi

# IMPORTANT: install into venv ONLY
"$SCRIPT_DIR/venv/bin/pip" install --upgrade pip
"$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

echo "✓ dependencies installed in venv"
echo ""

# ===== 4. Install systemd service =====
echo "[4/4] Installing service..."

sudo cp "$SCRIPT_DIR/yolov8-detection.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable yolov8-detection.service

echo "✓ service installed & enabled"

echo ""
echo "DONE ✔"
echo "Run: sudo systemctl start yolov8-detection.service"