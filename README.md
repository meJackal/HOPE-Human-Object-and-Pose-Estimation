# YOLOv8-Pose Detection System with Web UI

Real-time human pose detection using YOLOv8-Pose model with a web-based control interface.

## Features

- **Real-time pose detection** using YOLOv8n-pose model
- **Initialization page** with system status checks before detection
- **Web UI** with split layout:
  - Left: Live camera feed with pose overlay
  - Right: Control panel (status, start/stop, detection stats, logs)
- **WebSocket streaming** for real-time updates
- **REST API** for control commands
- **Auto-start capability** for Raspberry Pi embedded systems
- **Headless operation** - no display required on Raspberry Pi

## Quick Start

### 1. Install dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

The first run will download the YOLOv8n-pose model (~6MB).

### 2. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open the web UI

Navigate to http://localhost:8000/ in your browser.

You'll first see the **initialization page** that checks:
- Server connection status
- Model loading status  
- Camera readiness

Once all systems are ready, click "Start Detection System" to proceed to the detection interface.

### 4. Start detection

On the detection page, click the "Start Detection" button in the right panel. The system will:
- Initialize your webcam (or camera device 0)
- Run YOLOv8-Pose inference on each frame
- Display detected humans with skeleton overlay
- Show real-time count and FPS

## System Requirements

- Python 3.10+
- Webcam or USB camera
- For Raspberry Pi 5: 4GB+ RAM recommended

## API Endpoints

- `GET /` - Initialization page (home.html)
- `GET /detection` - Detection interface (detection.html)
- `GET /status` - System status
- `POST /start` - Start detection
- `POST /stop` - Stop detection
- `POST /log_detection` - Log detection event
- `GET /logs` - Retrieve detection logs
- `WebSocket /ws` - Real-time pose data stream

## Raspberry Pi Setup (Headless/Embedded System)

For deploying this on a Raspberry Pi that auto-starts without a display:

### How It Works

1. **Raspberry Pi boots up** → Backend server automatically starts
2. **From your laptop**, open browser: `http://<pi-ip>:8000`
3. **Enter Pi's IP address** → Frontend connects and checks status
4. **All systems ready** → Click "Start Detection System"
5. **Control remotely** → View camera feed and detections on your laptop

**✨ No HDMI, keyboard, or mouse needed on the Raspberry Pi!**

### Quick Setup

1. Transfer the entire project to your Raspberry Pi:
   ```bash
   scp -r Capstone pi@<raspberry-pi-ip>:/home/pi/
   ```

2. SSH into your Raspberry Pi and run the setup script:
   ```bash
   cd /home/pi/Capstone/backend
   chmod +x setup_raspberry_pi.sh
   ./setup_raspberry_pi.sh
   ```

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Configure auto-start service
- Start the server immediately

### Access from Other Devices

Once running on the Raspberry Pi, access it from any device on the same network:

**Option 1: Using Hostname (Recommended)**
```
http://raspberrypi.local:8000
```
✅ Works even if IP address changes  
✅ No configuration needed

**Option 2: Using IP Address**
```
http://<raspberry-pi-ip>:8000
```
Example: `http://192.168.1.100:8000`

The system runs headless - no display needed on the Pi!

### Detailed Instructions

See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for:
- Manual setup steps
- Service management commands
- Troubleshooting guide
- Configuration options

## Next Steps for Raspberry Pi Integration

Additional enhancements you can add:

1. **Pi Camera support**: Configure to use Raspberry Pi Camera Module instead of USB camera
2. **Optimize model**: Convert to ONNX or TFLite for better performance on ARM
3. **Add MQTT**: Integrate IoT messaging for remote control and alerts
4. **Security**: Add authentication and HTTPS for production deployment
5. **Persistent storage**: Configure database for long-term detection logs

## Troubleshooting

**No camera detected:**
- Check camera permissions
- Verify camera device index (try 0, 1, 2...)
- For Pi Camera, ensure `libcamera` support

**Slow performance:**
- Use a smaller model or reduce frame resolution
- Consider model optimization (quantization, ONNX Runtime)
- Lower the target FPS in the backend

## Project Structure

```
Capstone/
├── README.md                         # Main documentation
├── RASPBERRY_PI_SETUP.md            # Detailed Pi setup guide
├── backend/
│   ├── main.py                      # FastAPI server
│   ├── requirements.txt             # Python dependencies
│   ├── yolov8n-pose.pt             # YOLOv8 pose model
│   ├── start_server.sh             # Auto-start script
│   ├── setup_raspberry_pi.sh       # Quick setup script
│   └── yolov8-detection.service    # Systemd service file
├── frontend/
│   ├── home.html                   # Initialization page
│   └── detection.html              # Detection interface
└── logs/
    ├── detections.json             # Detection event logs
    ├── startup.log                 # Server startup logs
    ├── service.log                 # Systemd service logs
    └── service_error.log           # Error logs
```
