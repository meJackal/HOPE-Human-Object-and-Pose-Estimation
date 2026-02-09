import asyncio
import json
import base64
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from ultralytics import YOLO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix for PyTorch 2.6+ weights_only default
try:
    from ultralytics.nn.tasks import PoseModel
    torch.serialization.add_safe_globals([PoseModel])
except Exception as e:
    logger.warning(f"Could not add safe globals: {e}")

app = FastAPI()

# Serve the frontend files from /static and return index at /
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_FILE = LOGS_DIR / "detections.json"

# Create logs directory
LOGS_DIR.mkdir(exist_ok=True)
if not LOGS_FILE.exists():
    LOGS_FILE.write_text(json.dumps([]))
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Global state
model: Optional[YOLO] = None
is_running = False
camera: Optional[cv2.VideoCapture] = None


def init_model():
    global model
    if model is None:
        # Download YOLOv8n-pose model (smallest, fastest)
        logger.info("Loading YOLOv8n-pose model...")
        try:
            model = YOLO("yolov8n-pose.pt")
        except Exception as e:
            # Fallback: try with torch.load weights_only workaround
            logger.warning(f"Standard load failed: {e}")
            logger.info("Attempting alternative loading method...")
            import torch
            # Temporarily disable weights_only check
            original_load = torch.load
            torch.load = lambda *args, **kwargs: original_load(*args, **{**kwargs, 'weights_only': False})
            try:
                model = YOLO("yolov8n-pose.pt")
            finally:
                torch.load = original_load
        logger.info("Model loaded successfully")
    return model


def init_camera(source=0):
    global camera
    if camera is None or not camera.isOpened():
        logger.info(f"Attempting to open camera device {source}...")
        # Try different backends
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            camera = cv2.VideoCapture(source, backend)
            if camera.isOpened():
                logger.info(f"Camera opened successfully with backend {backend}")
                # Use lower resolution for faster capture and processing
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer lag
                camera.set(cv2.CAP_PROP_FPS, 30)
                # Test read
                ret, test_frame = camera.read()
                if ret:
                    logger.info(f"Test frame captured: {test_frame.shape}")
                    return camera
                else:
                    logger.warning(f"Camera opened but cannot read frames")
                    camera.release()
                    camera = None
            else:
                logger.warning(f"Failed to open camera with backend {backend}")
        
        if camera is None or not camera.isOpened():
            raise RuntimeError(f"Cannot open camera device {source}. Please check camera permissions and connections.")
    return camera


@app.get("/")
async def root():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


@app.get("/status")
async def status():
    return JSONResponse({
        "status": "ok",
        "is_running": is_running,
        "model_loaded": model is not None,
        "camera_open": camera is not None and camera.isOpened()
    })


@app.post("/start")
async def start_detection():
    global is_running
    is_running = True
    return JSONResponse({"status": "started", "is_running": is_running})


@app.post("/stop")
async def stop_detection():
    global is_running
    is_running = False
    return JSONResponse({"status": "stopped", "is_running": is_running})


@app.post("/log_detection")
async def log_detection(data: dict):
    """Log human detection with timestamp"""
    try:
        # Read existing logs
        logs = json.loads(LOGS_FILE.read_text()) if LOGS_FILE.exists() else []
        
        # Calculate confidence-based counts
        persons = data.get("persons", [])
        high_conf_count = sum(1 for p in persons if p.get("bbox_conf", 0) >= 0.5)
        low_conf_count = sum(1 for p in persons if p.get("bbox_conf", 0) < 0.5)
        
        # Generate detection message
        detection_message = ""
        if high_conf_count > 0:
            detection_message = f"High chance - {high_conf_count} human(s) detected"
        if low_conf_count > 0:
            if detection_message:
                detection_message += f" | Low chance - {low_conf_count} possible human(s) in area"
            else:
                detection_message = f"Low chance - {low_conf_count} possible human(s) in area"
        
        # Add new detection
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "count": data.get("count", 0),
            "high_confidence_count": high_conf_count,
            "low_confidence_count": low_conf_count,
            "detection_message": detection_message,
            "persons": data.get("persons", [])
        }
        logs.append(log_entry)
        
        # Keep only last 100 logs
        logs = logs[-100:]
        
        # Save logs
        LOGS_FILE.write_text(json.dumps(logs, indent=2))
        
        return JSONResponse({"status": "logged", "entry": log_entry})
    except Exception as e:
        logger.error(f"Failed to log detection: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/logs")
async def get_logs(limit: int = 10):
    """Get recent detection logs"""
    try:
        logs = json.loads(LOGS_FILE.read_text()) if LOGS_FILE.exists() else []
        return JSONResponse({"logs": logs[-limit:][::-1]})  # Most recent first
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return JSONResponse({"logs": []})


@app.websocket("/ws")
async def websocket_pose(ws: WebSocket):
    global is_running
    await ws.accept()
    logger.info("WebSocket connection established")
    
    # Initialize model and camera
    try:
        logger.info("Initializing model...")
        init_model()
        logger.info("Initializing camera...")
        cap = init_camera()
        logger.info("Initialization complete")
    except Exception as e:
        error_msg = f"Failed to initialize: {str(e)}"
        logger.error(error_msg)
        await ws.send_text(json.dumps({"error": error_msg}))
        await ws.close()
        return
    
    try:
        frame_count = 0
        inference_skip = 4  # Run inference every N frames (higher = faster FPS but less frequent detection)
        send_skip = 1  # Send every N frames (reduces network overhead)
        last_persons = []  # Cache last detection results
        
        while True:
            if is_running and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    error_msg = "Failed to read frame from camera"
                    logger.error(error_msg)
                    await ws.send_text(json.dumps({"error": error_msg}))
                    await asyncio.sleep(0.1)
                    continue
                
                frame_count += 1
                if frame_count == 1:
                    logger.info(f"First frame captured: {frame.shape}")
                
                # Run inference only every N frames for better FPS
                persons = last_persons
                if frame_count % inference_skip == 0:
                    # Run YOLOv8-Pose inference with aggressive optimizations for speed
                    results = model(frame, verbose=False, imgsz=192, half=False, device='cuda' if torch.cuda.is_available() else 'cpu')
                
                    # Extract pose data with confidence filtering
                    persons = []
                    BBOX_CONF_THRESHOLD = 0.25  # Minimum confidence for person detection
                    KEYPOINT_CONF_THRESHOLD = 0.3  # Minimum confidence for keypoint visibility
                    
                    if len(results) > 0 and results[0].keypoints is not None:
                        keypoints_data = results[0].keypoints
                        boxes_data = results[0].boxes
                        
                        for i in range(len(keypoints_data)):
                            # Get bounding box confidence first
                            bbox = boxes_data[i].xyxy.cpu().numpy()[0]  # [x1, y1, x2, y2]
                            bbox_conf = float(boxes_data[i].conf.cpu().numpy()[0])
                        
                            # Skip detections with very low confidence
                            if bbox_conf < BBOX_CONF_THRESHOLD:
                                continue
                            
                            kp = keypoints_data[i].xy.cpu().numpy()[0]  # Shape: (17, 2)
                            conf = keypoints_data[i].conf.cpu().numpy()[0]  # Shape: (17,)
                        
                            # Format: [x, y, confidence] for each of 17 keypoints
                            # Only include keypoints with confidence above threshold
                            keypoints = []
                            for j in range(len(kp)):
                                kp_conf = float(conf[j])
                                # Include keypoint data but mark low confidence ones
                                if kp_conf >= KEYPOINT_CONF_THRESHOLD:
                                    keypoints.append([float(kp[j][0]), float(kp[j][1]), kp_conf])
                                else:
                                    # Set coordinates to 0 for low-confidence keypoints
                                    keypoints.append([0.0, 0.0, kp_conf])
                        
                            # Determine confidence level message
                            if bbox_conf >= 0.5:
                                confidence_message = "High chance - Human detected"
                            else:
                                confidence_message = "Low chance - Possible human in area"
                            
                            persons.append({
                                "id": i,
                                "keypoints": keypoints,
                                "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                                "bbox_conf": bbox_conf,
                                "confidence_message": confidence_message
                            })
                    
                    last_persons = persons  # Cache results for skipped frames
                
                # Skip sending some frames to reduce network overhead
                if frame_count % send_skip != 0:
                    await asyncio.sleep(0)
                    continue
                
                # No need to downscale since we're already capturing at 320x240
                display_frame = frame
                
                # Encode frame as JPEG with low quality for speed
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
                _, buffer = cv2.imencode('.jpg', display_frame, encode_param)
                frame_b64 = base64.b64encode(buffer).decode('utf-8')
                
                # Determine overall detection message
                detection_message = ""
                if persons:
                    high_conf_count = sum(1 for p in persons if p["bbox_conf"] >= 0.5)
                    low_conf_count = len(persons) - high_conf_count
                    
                    if high_conf_count > 0:
                        detection_message = f"High chance - {high_conf_count} human(s) detected"
                    if low_conf_count > 0:
                        if detection_message:
                            detection_message += f" | Low chance - {low_conf_count} possible human(s) in area"
                        else:
                            detection_message = f"Low chance - {low_conf_count} possible human(s) in area"
                
                payload = {
                    "width": display_frame.shape[1],
                    "height": display_frame.shape[0],
                    "persons": persons,
                    "frame": frame_b64,
                    "detection_message": detection_message
                }
                
                await ws.send_text(json.dumps(payload))
                # No sleep - let it run as fast as possible
                await asyncio.sleep(0)
            else:
                # Send idle status
                await ws.send_text(json.dumps({"idle": True, "is_running": is_running}))
                await asyncio.sleep(0.5)
                
    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_text(json.dumps({"error": str(e)}))
        return
