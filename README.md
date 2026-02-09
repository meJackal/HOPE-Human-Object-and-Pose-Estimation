# YOLOv8-Pose Detection System with Web UI

Real-time human pose detection using YOLOv8-Pose model with a web-based control interface.

## Features

- **Real-time pose detection** using YOLOv8n-pose model
- **Web UI** with split layout:
  - Left: Live camera feed with pose overlay
  - Right: Control panel (status, start/stop, detection stats)
- **WebSocket streaming** for real-time updates
- **REST API** for control commands

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

### 4. Start detection

Click the "Start Detection" button in the right panel. The system will:
- Initialize your webcam (or camera device 0)
- Run YOLOv8-Pose inference on each frame
- Display detected humans with skeleton overlay
- Show real-time count and FPS

## System Requirements

- Python 3.10+
- Webcam or USB camera
- For Raspberry Pi 5: 4GB+ RAM recommended

## API Endpoints

- `GET /` - Web UI
- `GET /status` - System status
- `POST /start` - Start detection
- `POST /stop` - Stop detection
- `WebSocket /ws` - Real-time pose data stream

## Next Steps for Raspberry Pi Integration

When you have your Raspberry Pi 5:

1. **Transfer this code** to the Pi
2. **Install dependencies** (consider using a virtual environment)
3. **Update camera source** in `backend/main.py` if using Pi Camera:
   ```python
   camera = cv2.VideoCapture(0)  # Change to appropriate device
   ```
4. **Optimize model**: Convert to ONNX or TFLite for better performance
5. **Add MQTT**: Integrate IoT messaging for remote control
6. **Security**: Add authentication and HTTPS for production

## Troubleshooting

**No camera detected:**
- Check camera permissions
- Verify camera device index (try 0, 1, 2...)
- For Pi Camera, ensure `libcamera` support

**Slow performance:**
- Use a smaller model or reduce frame resolution
- Consider model optimization (quantization, ONNX Runtime)
- Lower the target FPS in the backend
