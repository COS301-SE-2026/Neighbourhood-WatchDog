import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from pipeline.utils.thumbnail import annotate_frame, encode_frame_as_jpeg
import httpx
from datetime import datetime, timezone
import logging

logger = logging.getLogger("watchdog.ai")

app = FastAPI(title="WatchDog AI Service")

stream_router = APIRouter(prefix="/stream", tags=["stream"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

model = YOLO("pipeline/models/weights/yolov8n.pt")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def annotated_mjpeg(rtsp_url: str):
    tracker = DeepSort(
        max_age=70,
        n_init=2,
        max_iou_distance=0.7,
        embedder="mobilenet",
        embedder_gpu=False,
    )

    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        return

    frame_count = 0
    alerted_ids = set()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % 2 != 0:
                continue

            results = model.predict(frame, imgsz=640, conf=0.6, iou=0.3, classes=[0], verbose=False)

            detections = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                detections.append(([x1, y1, x2 - x1, y2 - y1], conf, "person"))

            tracks = tracker.update_tracks(detections, frame=frame)

            # Same conversion as test_detector.py
            tracks_for_thumbnail = []
            for track in tracks:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                left, top, right, bottom = track.to_ltrb()
                tracks_for_thumbnail.append({
                    "track_id": track.track_id,
                    "confidence": float(track.det_conf) if track.det_conf is not None else 0.0,
                    "bbox": [left, top, right, bottom],
                })

                if track_id not in alerted_ids and track.det_conf is not None:
                    alerted_ids.add(track_id)
                    logger.info(f"New person detected - Track ID: {track_id}, Confidence: {track.det_conf:.2f}")
                    try:
                        httpx.post(f"{BACKEND_URL}/alerts/", json={
                            "detection_type": "HUMAN_PRESENCE",
                            "confidence": float(track.det_conf),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                        logger.info(f"Alert sent for Track ID: {track_id}")
                    except Exception as e:
                        logger.error(f"Failed to send alert for Track ID {track_id}: {e}")

            annotated = annotate_frame(frame, tracks_for_thumbnail)
            jpeg_bytes = encode_frame_as_jpeg(annotated)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )
    finally:
        cap.release()


@stream_router.get("")
def stream_annotated(url: str = Query(..., description="RTSP URL")):
    return StreamingResponse(
        annotated_mjpeg(url),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

@stream_router.get("/health")
def stream_health(url: str = Query(..., description="RTSP URL")):
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    available = cap.isOpened()
    if available:
        ret, _ = cap.read()
        available = ret
    cap.release()
    return {"available": available, "url": url}


app.include_router(stream_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai"}