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
from pipeline.utils.zone_config import filter_detections_by_zones
import httpx
from datetime import datetime, timezone
import logging
import threading


logger = logging.getLogger("watchdog.ai")
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

threat_model = YOLO("pipeline/models/weights/best.pt")
person_model = YOLO("pipeline/models/weights/yolov8n.pt")



#cache for the camera settings, refresh every 30 seconds ---- still need to test
_camera_settings: dict =  {
    "confidence_threshold": 0.5,
    "zones": []
}
_settings_lock = threading.Lock()







BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CAMERA_ID = "2"
NEIGHBOURHOOD_ID = "10000000-0000-0000-0000-000000000001"
RTSP_URL = os.getenv("RTSP_URL", "rtsp://Intrepid:password1234@192.168.3.68:554/stream2")



def _fetch_camera_settings(backend_url: str, camera_id: str) -> None:

    #fetching the zone and threshold settings from the backend, and then updating the cache

    try:
        resp = httpx.get(
            f"{backend_url}/cameras/{camera_id}/settings",

            headers={
                "Authorization": "Bearer mock-token",
                "X-Mock-Role": "NEIGHBOURHOOD_ADMIN",
                "X-Mock-Sub": "20000000-0000-0000-0000-000000000001"
                    
                },

            timeout=2.0

        )


        if resp.status_code == 200:
            data = resp.json()
            with _settings_lock:
                _camera_settings["confidence_threshold"] = data.get("confidence_threshold", 0.5)
                _camera_settings["zones"] = [
                    z["polygon"]
                    for z in data.get("zones", [])

                ]

    except Exception:
        pass #we can keep using the cached settings on failure



def _settings_refresh_loop(backend_url: str, camera_id: str) -> None:

    #refresh camera settings every 30 seconds
    while True:
        _fetch_camera_settings(backend_url, camera_id)
        time.sleep(30)


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


def _extract_detections(frame) -> tuple:
    """Convert YOLO results to DeepSort detection format."""


    #running yolo on frame, applying the confidendce threshold and zone filters
    with _settings_lock:
        threshold = _camera_settings["confidence_threshold"]
        zones = list(_camera_settings["zones"])


    frame_h, frame_w = frame.shape[:2]

    #only passing human objects to deepsort
    person_detections = []
    weapon_detections = []

    #threat detection
    threat_results = threat_model.predict(
        frame,
        imgsz=640,
        conf=threshold,
        verbose=False
    )

    for box in threat_results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])

        label = threat_model.names[int(box.cls[0])] # represents gun, knife, grenade

        weapon_detections.append(([x1, y1, x2 - x1, y2 - y1], conf, label))



    #person detection
    person_results = person_model.predict(
        frame,
        imgsz=640,
        conf=threshold,
        classes=[0],
        verbose=False
        )
    
    for box in person_results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        person_detections.append(([x1, y1, x2 - x1, y2 - y1], conf, "person"))



    #applying the zones filter (current plan: pass all it no zones are configured)
    person_detections = filter_detections_by_zones(person_detections, zones, frame_w, frame_h)
    weapon_detections = filter_detections_by_zones(weapon_detections, zones, frame_w, frame_h)




    print(f"Threat boxes: {len(weapon_detections)}, Person boxes: {len(person_detections)}")
        
    
    return person_detections, weapon_detections


def _build_track_payload(track) -> dict:
    """Convert a confirmed DeepSort track to the annotation payload format."""
    left, top, right, bottom = track.to_ltrb()

    detection_type = track.get_det_class() or "person"


    return {
        "track_id": track.track_id,
        "confidence": float(track.det_conf) if track.det_conf is not None else 0.0,
        "bbox": [left, top, right, bottom],
        "detection_type": detection_type,
    }


def _send_new_person_alert(track_id: int, conf: float, detection_type: str = "UNKNOWN") -> None:
    """Send a one-time human-presence alert to the backend."""
    try:
        httpx.post(
            f"{BACKEND_URL}/alerts/dev/broadcast",
            json={
                "camera_id": CAMERA_ID,
                "neighbourhood_id": NEIGHBOURHOOD_ID,
                "detection_type": detection_type.upper(), #GUN, KNIFE, GRENADE
                "confidence": conf,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "thumbnail_url": None,
            },
            timeout=1.0,
        )
    except Exception:
        logger.exception("Alert POST failed for Track ID %s", track_id)


def _open_stream(rtsp_url: str):
    """Open an RTSP stream, returning None if unavailable."""
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        cap = None
    return cap


def _detection_loop(rtsp_url: str) -> None:
    """
    Background thread: continuously read RTSP, run YOLO+DeepSort, push annotations.
    The frontend uses WebRTC from mediamtx for display; this loop supplies bounding boxes.
    """
    logger.info("Detection loop starting for %s", rtsp_url)

    tracker = DeepSort(
        max_age=150,
        n_init=3,
        max_iou_distance=0.5,  #for stricter matching and less duplicate boxes
        embedder="mobilenet",
        embedder_gpu=False,
        nms_max_overlap=0.5 #to suppress overlapping boxes
    )

    cap = None
    frame_count = 0
    alerted_ids: set = set()

    while True:
        cap = _reconnect_if_needed(cap, rtsp_url)
        if cap is None:
            continue

        ret, frame = cap.read()
        if not ret:
            logger.warning("Empty frame — reconnecting in 2s")
            cap.release()
            cap = None
            time.sleep(2)
            continue

        frame_count += 1
        if frame_count % 4 != 0:
            continue

        person_detections, weapon_detections = _extract_detections(frame)

        #only tracking humans through deepsort
        tracks = tracker.update_tracks(person_detections, frame=frame)

        tracks_payload = _collect_tracks(tracks, alerted_ids)


        #adding raw weapon detections (no deepsort, no duplication)
        for i, (bbox, conf, label) in enumerate(weapon_detections):
            x, y, w, h = bbox
 
            tracks_payload.append({
                "track_id": f"threat_{i}",
                "confidence": conf,
                "bbox": [x, y, x + w, y + h],
                "detection_type": label

            })



        #filtering out zero confidence (0%) ghost tracks
        tracks_payload = [t for t in tracks_payload 
                          if t.get("confidence", 0) > 0.1 or str(t.get("track_id", "")).startswith("threat_")]
            

        _push_annotations(BACKEND_URL, CAMERA_ID, tracks_payload, datetime.now(timezone.utc).isoformat())


def _reconnect_if_needed(cap, rtsp_url: str):
    """Return an open capture, reconnecting if necessary."""
    if cap is not None and cap.isOpened():
        return cap
    logger.info("Connecting to RTSP stream…")
    new_cap = _open_stream(rtsp_url)
    if new_cap is None:
        logger.warning("Could not open stream — retrying in 5s")
        time.sleep(5)
        return None
    logger.info("RTSP stream connected")
    return new_cap


def _collect_tracks(tracks, alerted_ids: set) -> list:
    """Build the annotation payload from confirmed tracks, firing alerts for new persons."""
    payload = []
    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id

        track_data = _build_track_payload(track)

        payload.append(track_data)

        if track_id not in alerted_ids and track.det_conf is not None:
            alerted_ids.add(track_id)

            detection_type = track.get_det_class() or "UNKNOWN"

            logger.info("New detection — Track ID: %s, conf: %.2f", detection_type, track_id, track.det_conf)
            _send_new_person_alert(track_id, float(track.det_conf), detection_type)
    return payload


@asynccontextmanager
async def lifespan(app_: FastAPI):
    """Start the detection background thread when the AI service starts."""

    #starting the detection loop
    t = threading.Thread(target=_detection_loop, args=(RTSP_URL,), daemon=True)
    t.start()


    #starting tne settings refresh loop
    s = threading.Thread(
        target=_settings_refresh_loop,
        args=(BACKEND_URL, CAMERA_ID),
        daemon=True
    )

    s.start()


    logger.info("Detection background thread started")
    yield


app = FastAPI(title="WatchDog AI Service", lifespan=lifespan)

stream_router = APIRouter(prefix="/stream", tags=["stream"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def annotated_mjpeg(rtsp_url: str):
    """MJPEG endpoint - useful for direct debugging/testing."""
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


            #weapon detection
            threat_results = threat_model.predict(frame, imgsz=640, conf=0.35, verbose=False)
            tracks_for_thumbnail = [
                {
                    "track_id": i, 
                    "confidence": float(box.conf[0]), 
                    "bbox": box.xyxy[0].tolist(),
                    "detection_type": threat_model.names[int(box.cls[0])],

                }
                for i, box in enumerate(threat_results[0].boxes)
            ]


            #human detection
            person_results = person_model.predict(frame, imgsz=640, conf=0.5, classes=[0], verbose=False)
            tracks_for_thumbnail += [
                {
                    "track_id": 100 + i,
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist(),
                    "detection_type": "person",

                }

                for i, box in enumerate(person_results[0].boxes)
            ]



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
