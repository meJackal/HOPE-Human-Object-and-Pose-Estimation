#!/bin/bash
# Startup script for YOLOv8 Pose Detection System
# This script should be run automatically on Raspberry Pi boot

# Define paths
PROJECT_DIR="/home/julius/Documents/Human-Detection"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/startup.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "=== Starting YOLOv8 Pose Detection System ==="

# Change to backend directory
cd "$BACKEND_DIR" || {
    log_message "ERROR: Cannot change to backend directory: $BACKEND_DIR"
    exit 1
}

log_message "Current directory: $(pwd)"

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    log_message "ERROR: Python3 not found"
    exit 1
fi

log_message "Python version: $(python3 --version)"

# Check if virtual environment exists
if [ -d "venv" ]; then
    log_message "Activating virtual environment..."
    source venv/bin/activate
    log_message "Virtual environment activated"
else
    log_message "WARNING: No virtual environment found at $BACKEND_DIR/venv"
    log_message "Running with system Python..."
fi

# Check if requirements are installed
log_message "Checking dependencies..."
python3 -c "import fastapi, cv2, torch, ultralytics" 2>/dev/null
if [ $? -ne 0 ]; then
    log_message "WARNING: Some dependencies may be missing"
    log_message "Installing requirements..."
    pip3 install -r requirements.txt | tee -a "$LOG_FILE"
fi

# Check if model file exists
if [ ! -f "yolov8n-pose.pt" ]; then
    log_message "WARNING: Model file yolov8n-pose.pt not found"
    log_message "Model will be downloaded on first run"
fi

# Get the Raspberry Pi's IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')
log_message "Raspberry Pi IP Address: $IP_ADDRESS"

# Start the FastAPI server with uvicorn
log_message "Starting FastAPI server..."
log_message "Access the system at: http://$IP_ADDRESS:8000"
log_message "Or from this device: http://localhost:8000"

# Run the server (this will block)
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info 2>&1 | tee -a "$LOG_FILE"

# If server stops unexpectedly
log_message "ERROR: Server stopped unexpectedly"
exit 1
