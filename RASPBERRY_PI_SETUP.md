# Raspberry Pi 5 — Installation & Setup

Target: Raspberry Pi 5 (64-bit). This guide walks through prerequisites, a quick automated setup (provided by the project), and manual steps to install and run the service.

Prerequisites

- Raspberry Pi 5 with 64-bit OS (Raspberry Pi OS 64-bit or Ubuntu 22.04/24.04 ARM64)
- SSH access to the Pi and network connectivity
- USB camera or Raspberry Pi Camera Module (for Pi Camera use `libcamera` stack)
- 4 GB+ RAM recommended

Quick (automated) setup

1. Copy repository to the Pi (from your laptop):

```bash
scp -r Human-Detection pi@<raspberry-pi-ip>:/home/pi/
```

2. SSH into the Pi and run the included setup script:

```bash
ssh pi@<raspberry-pi-ip>
cd /home/pi/Human-Detection/backend
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
```

What the script does (typical):

- Creates a Python virtual environment and installs `requirements.txt`.
- Downloads or ensures the YOLOv8 model is available.
- Installs required system packages (e.g., `libcamera`, `ffmpeg`) when needed.
- Registers and enables a `systemd` service (`yolov8-detection.service`) to auto-start on boot.

Manual install (if you prefer control)

1. Update packages and install required system tools:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip ffmpeg libatlas-base-dev libjpeg-dev
```

2. Create venv and install Python packages:

```bash
cd /home/pi/Human-Detection/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. (Optional) If using Pi Camera, ensure `libcamera` is installed and enabled.

4. Start server manually:

```bash
cd /home/pi/Human-Detection/backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Systemd service (manage auto-start)

If the automated setup created the service, use:

```bash
sudo systemctl start yolov8-detection
sudo systemctl enable yolov8-detection
sudo systemctl status yolov8-detection
sudo journalctl -u yolov8-detection -f
```

Network & access

- Open a browser on another device in the same network and visit:
  - `http://raspberrypi.local:8000` (if mDNS/hostname discovery works)
  - or `http://<raspberry-pi-ip>:8000`

Troubleshooting

- Camera not detected: run `ls /dev/video*` and test with `ffmpeg -f v4l2 -list_formats all -i /dev/video0` or `libcamera-hello`.
- Model fails to load: confirm Python packages installed in the venv and inspect server logs.
- Service won't start: check `sudo journalctl -u yolov8-detection` and the service file path permissions.

Performance tips

- Lower camera resolution or input FPS to reduce CPU usage.
- Use `yolov8n-pose` (nano) for better real-time performance.
- Consider converting the model to ONNX or TFLite for improved ARM performance.

If you want, I can tailor this guide to include exact commands used by `setup_raspberry_pi.sh` or create a troubleshooting checklist specific to your Pi image.
