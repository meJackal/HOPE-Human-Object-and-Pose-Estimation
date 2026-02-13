#!/bin/bash
# Quick setup script for Raspberry Pi
# Run this script after transferring the project to Raspberry Pi

echo "======================================"
echo "YOLOv8 Detection System - Quick Setup"
echo "======================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"
echo ""

# Step 1: Make start_server.sh executable
echo "[1/5] Making start_server.sh executable..."
chmod +x "$SCRIPT_DIR/start_server.sh"
echo "✓ Done"
echo ""

# Step 2: Update service file paths
echo "[2/5] Updating service file with correct paths..."
sed -i "s|/home/pi/Capstone|$PROJECT_DIR|g" "$SCRIPT_DIR/yolov8-detection.service"
echo "✓ Done"
echo ""

# Step 3: Install Python dependencies
echo "[3/5] Setting up Python environment..."
read -p "Do you want to create a virtual environment? (recommended) [Y/n]: " create_venv
create_venv=${create_venv:-Y}

if [[ $create_venv =~ ^[Yy]$ ]]; then
    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$SCRIPT_DIR/venv"
        echo "✓ Virtual environment created"
    else
        echo "Virtual environment already exists"
    fi
    
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
    
    echo "Installing dependencies..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
    echo "✓ Dependencies installed"
else
    echo "Skipping virtual environment creation"
    echo "Installing dependencies with system Python..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi
echo ""

# Step 4: Install systemd service
echo "[4/5] Installing systemd service..."
read -p "Install service for auto-start on boot? [Y/n]: " install_service
install_service=${install_service:-Y}

if [[ $install_service =~ ^[Yy]$ ]]; then
    sudo cp "$SCRIPT_DIR/yolov8-detection.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable yolov8-detection.service
    echo "✓ Service installed and enabled"
    echo ""
    
    read -p "Start the service now? [Y/n]: " start_now
    start_now=${start_now:-Y}
    
    if [[ $start_now =~ ^[Yy]$ ]]; then
        sudo systemctl start yolov8-detection.service
        echo "✓ Service started"
        sleep 2
        echo ""
        echo "Service status:"
        sudo systemctl status yolov8-detection.service --no-pager
    fi
else
    echo "Skipping service installation"
fi
echo ""

# Step 5: Display access information
echo "[5/5] Setup complete!"
echo ""
echo "======================================"
echo "Access Information"
echo "======================================"
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo "Raspberry Pi IP: $IP_ADDRESS"
echo ""
echo "Access the system from:"
echo "  - This device: http://localhost:8000"
echo "  - Other devices: http://$IP_ADDRESS:8000"
echo ""
echo "======================================"
echo "Useful Commands"
echo "======================================"
echo "Check service status:"
echo "  sudo systemctl status yolov8-detection.service"
echo ""
echo "View logs:"
echo "  sudo journalctl -u yolov8-detection.service -f"
echo ""
echo "Stop service:"
echo "  sudo systemctl stop yolov8-detection.service"
echo ""
echo "Restart service:"
echo "  sudo systemctl restart yolov8-detection.service"
echo ""
echo "Manual start (for testing):"
echo "  cd $SCRIPT_DIR && ./start_server.sh"
echo ""
echo "======================================"
