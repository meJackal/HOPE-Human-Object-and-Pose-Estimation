import asyncio
import json
import base64
import threading
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_FILE = LOGS_DIR / "detections.json"

LOGS_DIR.mkdir(exist_ok=True)
if not LOGS_FILE.exists():
    LOGS_FILE.write_text(json.dumps([]))

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

model: Optional[YOLO] = None
latest_frame: Optional[bytes] = None
latest_persons = []
is_running = False
lock = threading.Lock()
camera_thread = None
stop_event = threading.Event()


def init_model():
    global model
    if model is None:
        logger.info("Loading YOLOv8n-pose model...")
        model = YOLO("yolov8n-pose.pt")
        logger.info("Model loaded successfully")
    return model


def camera_loop():
    global latest_frame, latest_persons

    logger.info("Camera thread starting...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Failed to open camera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 30)
    logger.info(f"Camera opened: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")

    init_model()

    frame_count = 0
    inference_skip = 15

    try:
        while not stop_event.is_set():
            if not is_running:
                stop_event.wait(0.1)
                continue

            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame")
                continue

            frame_count += 1

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
            _, buffer = cv2.imencode(".jpg", frame, encode_param)
            frame_bytes = base64.b64encode(buffer).decode("utf-8")

            if frame_count % inference_skip == 0:
                try:
                    results = model(
                        frame,
                        imgsz=192,
                        conf=0.35,
                        iou=0.7,
                        device="cpu",
                        verbose=False,
                        max_det=5,
                    )

                    persons = []
                    BBOX_CONF_THRESHOLD = 0.35
                    KEYPOINT_CONF_THRESHOLD = 0.3

                    if results and results[0].keypoints is not None:
                        keypoints_data = results[0].keypoints
                        boxes_data = results[0].boxes

                        for i in range(len(keypoints_data)):
                            bbox = boxes_data[i].xyxy.cpu().numpy()[0]
                            bbox_conf = float(boxes_data[i].conf.cpu().numpy()[0])

                            if bbox_conf < BBOX_CONF_THRESHOLD:
                                continue

                            kp = keypoints_data[i].xy.cpu().numpy()[0]
                            conf = keypoints_data[i].conf.cpu().numpy()[0]

                            keypoints = []
                            for j in range(len(kp)):
                                kp_conf = float(conf[j])
                                if kp_conf >= KEYPOINT_CONF_THRESHOLD:
                                    keypoints.append([float(kp[j][0]), float(kp[j][1]), kp_conf])
                                else:
                                    keypoints.append([0.0, 0.0, kp_conf])

                            confidence_message = (
                                "High chance - Human detected"
                                if bbox_conf >= 0.5
                                else "Low chance - Possible human in area"
                            )

                            persons.append({
                                "id": i,
                                "keypoints": keypoints,
                                "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                                "bbox_conf": bbox_conf,
                                "confidence_message": confidence_message,
                            })

                    with lock:
                        latest_persons = persons

                except Exception as e:
                    logger.error(f"Inference error: {e}")

            with lock:
                latest_frame = frame_bytes

    finally:
        cap.release()
        logger.info("Camera thread stopped")


def start_camera_thread():
    global camera_thread

    if camera_thread is not None and camera_thread.is_alive():
        logger.info("Camera thread already running")
        return

    stop_event.clear()
    camera_thread = threading.Thread(target=camera_loop, daemon=True)
    camera_thread.start()
    logger.info("Camera thread started")


def stop_camera_thread():
    global camera_thread

    if camera_thread is None or not camera_thread.is_alive():
        return

    stop_event.set()
    camera_thread.join(timeout=2.0)
    logger.info("Camera thread stopped")


@app.on_event("startup")
async def startup_event():
    start_camera_thread()


@app.on_event("shutdown")
async def shutdown_event():
    global is_running
    is_running = False
    stop_camera_thread()


@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "home.html"))


@app.get("/detection")
async def detection():
    return FileResponse(str(FRONTEND_DIR / "detection.html"))


@app.get("/status")
async def status():
    return JSONResponse({
        "status": "ok",
        "is_running": is_running,
        "model_loaded": model is not None,
        "camera_thread_alive": camera_thread is not None and camera_thread.is_alive(),
    })


@app.post("/start")
async def start_detection():
    global is_running
    is_running = True
    start_camera_thread()
    logger.info("Detection started")
    return JSONResponse({"status": "started", "is_running": is_running})


@app.post("/stop")
async def stop_detection():
    global is_running
    is_running = False
    logger.info("Detection stopped")
    return JSONResponse({"status": "stopped", "is_running": is_running})


@app.post("/log_detection")
async def log_detection(data: dict):
    try:
        logs = []
        if LOGS_FILE.exists():
            try:
                content = LOGS_FILE.read_text().strip()
                if content:
                    logs = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Corrupted log file, resetting: {e}")

        persons = data.get("persons", [])
        high_conf_count = sum(1 for p in persons if p.get("bbox_conf", 0) >= 0.5)
        low_conf_count = sum(1 for p in persons if p.get("bbox_conf", 0) < 0.5)

        detection_message = ""
        if high_conf_count > 0:
            detection_message = f"High chance - {high_conf_count} human(s) detected"
        if low_conf_count > 0:
            suffix = f"Low chance - {low_conf_count} possible human(s) in area"
            detection_message = f"{detection_message} | {suffix}" if detection_message else suffix

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "count": data.get("count", 0),
            "high_confidence_count": high_conf_count,
            "low_confidence_count": low_conf_count,
            "detection_message": detection_message,
            "persons": persons,
        }
        logs.append(log_entry)
        logs = logs[-100:]
        LOGS_FILE.write_text(json.dumps(logs, indent=2))

        return JSONResponse({"status": "logged", "entry": log_entry})
    except Exception as e:
        logger.error(f"Failed to log detection: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/logs")
async def get_logs(limit: int = 10):
    try:
        logs = []
        if LOGS_FILE.exists():
            try:
                content = LOGS_FILE.read_text().strip()
                if content:
                    logs = json.loads(content)
            except json.JSONDecodeError:
                logger.warning("Corrupted log file, returning empty logs")
        return JSONResponse({"logs": logs[-limit:][::-1]})
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return JSONResponse({"logs": []})


@app.websocket("/ws")
async def websocket_pose(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            if is_running:
                with lock:
                    persons_copy = latest_persons.copy()
                    frame_copy = latest_frame

                detection_message = ""
                if persons_copy:
                    high_conf_count = sum(1 for p in persons_copy if p["bbox_conf"] >= 0.5)
                    low_conf_count = len(persons_copy) - high_conf_count

                    if high_conf_count > 0:
                        detection_message = f"High chance - {high_conf_count} human(s) detected"
                    if low_conf_count > 0:
                        suffix = f"Low chance - {low_conf_count} possible human(s) in area"
                        detection_message = f"{detection_message} | {suffix}" if detection_message else suffix

                payload = {
                    "width": CAMERA_WIDTH,
                    "height": CAMERA_HEIGHT,
                    "persons": persons_copy,
                    "frame": frame_copy,
                    "detection_message": detection_message,
                }

                await ws.send_text(json.dumps(payload))
                await asyncio.sleep(0.033)  # ~30 FPS
            else:
                await ws.send_text(json.dumps({"idle": True, "is_running": is_running}))
                await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws.send_text(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)