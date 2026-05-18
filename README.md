# Human Object and Pose Estimation

H.O.P.E is a compact, embedded-style human pose detection system built to run headless on a Raspberry Pi 5. It pairs a FastAPI backend that captures camera frames and runs Ultralytics `yolov8n-pose` inference with a lightweight browser-based frontend for remote control and visualization.

## Features

- Real-time pose detection using YOLOv8-pose model
- Initialization page with system status checks before detection
- Web UI with split layout:
   - Left: Live camera feed with pose overlay
   - Right: Control panel (status, start/stop, detection stats, logs)
- WebSocket streaming for real-time updates
- REST API for control commands
- Auto-start capability for Raspberry Pi embedded systems
- Headless operation - no display required on Raspberry Pi

## System Requirements

- Python 3.10+
- Webcam or USB camera
- For Raspberry Pi 5: 4GB+ RAM recommended
