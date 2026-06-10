import os
import cv2
import time
import threading
from contextlib import asynccontextmanager
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
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

model = YOLO("pipeline/models/weights/yolov8n.pt")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CAMERA_ID = "2"
NEIGHBOURHOOD_ID = "10000000-0000-0000-0000-000000000001"
RTSP_URL = os.getenv("RTSP_URL", "rtsp://Intrepid:password1234@192.168.1.126:554/stream2")


def _push_annotations(backend_url: str, camera_id: str, tracks: list, timestamp: str) -> None:
    """Fire-and-forget: POST track data to backend so it can broadcast via WebSocket."""
    try:
        httpx.post(
            f"{backend_url}/api/stream/cameras/{camera_id}/annotations",
            json={"tracks": tracks, "timestamp": timestamp},
            timeout=0.5,
        )
    except Exception:
        pass


def _detection_loop(rtsp_url: str) -> None:
    """
    Background thread: continuously read RTSP, run YOLO+DeepSort, push annotations.
    This is the main loop — the frontend uses WebRTC from mediamtx for display,
    and this loop feeds bounding boxes to the backend WebSocket broadcaster.
    """
    logger.info(f"Detection loop starting for {rtsp_url}")

    tracker = DeepSort(
        max_age=70,
        n_init=2,
        max_iou_distance=0.7,
        embedder="mobilenet",
        embedder_gpu=False,
    )

    cap = None
    frame_count = 0
    alerted_ids = set()

    while True:
        # (Re)connect to the RTSP stream
        if cap is None or not cap.isOpened():
            logger.info("Connecting to RTSP stream…")
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                logger.warning("Could not open stream — retrying in 5s")
                time.sleep(5)
                cap = None
                continue
            logger.info("RTSP stream connected")

        ret, frame = cap.read()
        if not ret:
            logger.warning("Empty frame — reconnecting in 2s")
            cap.release()
            cap = None
            time.sleep(2)
            continue

        frame_count += 1
        if frame_count % 2 != 0:   # process every other frame
            continue

        results = model.predict(frame, imgsz=640, conf=0.6, iou=0.3, classes=[0], verbose=False)

        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, "person"))

        tracks = tracker.update_tracks(detections, frame=frame)

        tracks_payload = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            left, top, right, bottom = track.to_ltrb()
            tracks_payload.append({
                "track_id": track_id,
                "confidence": float(track.det_conf) if track.det_conf is not None else 0.0,
                "bbox": [left, top, right, bottom],
            })

            # Fire alert for new unique person
            if track_id not in alerted_ids and track.det_conf is not None:
                alerted_ids.add(track_id)
                logger.info(f"New person — Track ID: {track_id}, conf: {track.det_conf:.2f}")
                try:
                    httpx.post(f"{BACKEND_URL}/alerts/dev/broadcast", json={
                        "camera_id": CAMERA_ID,
                        "neighbourhood_id": NEIGHBOURHOOD_ID,
                        "detection_type": "HUMAN_PRESENCE",
                        "confidence": float(track.det_conf),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "thumbnail_url": None,
                    }, timeout=1.0)
                except Exception as e:
                    logger.error(f"Alert POST failed: {e}")

        # Push annotation data to backend → WebSocket → frontend canvas
        _push_annotations(
            BACKEND_URL, CAMERA_ID, tracks_payload,
            datetime.now(timezone.utc).isoformat()
        )


@asynccontextmanager
async def lifespan(app_: FastAPI):
    """Start the detection background thread when the AI service starts."""
    t = threading.Thread(target=_detection_loop, args=(RTSP_URL,), daemon=True)
    t.start()
    logger.info("Detection background thread started")
    yield
    # daemon=True means it dies with the process — no explicit cleanup needed


app = FastAPI(title="WatchDog AI Service", lifespan=lifespan)

stream_router = APIRouter(prefix="/stream", tags=["stream"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def annotated_mjpeg(rtsp_url: str):
    """MJPEG endpoint — useful for direct debugging/testing."""
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        return
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % 2 != 0:
                continue
            results = model.predict(frame, imgsz=640, conf=0.6, iou=0.3, classes=[0], verbose=False)
            tracks_for_thumbnail = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                tracks_for_thumbnail.append({
                    "track_id": 0,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                })
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