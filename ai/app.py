import os
import cv2
from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from pipeline.utils.thumbnail import annotate_frame, encode_frame_as_jpeg

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

app = FastAPI(title="WatchDog AI Service")

stream_router = APIRouter(prefix="/stream", tags=["stream"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

model = YOLO("pipeline/models/weights/yolov8n.pt")


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
                left, top, right, bottom = track.to_ltrb()
                tracks_for_thumbnail.append({
                    "track_id": track.track_id,
                    "confidence": float(track.det_conf) if track.det_conf is not None else 0.0,
                    "bbox": [left, top, right, bottom],
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