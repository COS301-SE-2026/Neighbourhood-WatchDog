from camera_runtime import CameraSpec, CameraSupervisor

import os
import cv2
import time
import threading
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from pipeline.utils.thumbnail import annotate_frame, encode_frame_as_jpeg
from pipeline.utils.zone_config import filter_detections_by_zones
from pipeline.processing.alert_confirmation import is_track_ready_to_alert

import httpx
import logging
import keyring
import boto3

logger = logging.getLogger("watchdog.ai")
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = ("rtsp_transport;tcp|fflags;nobuffer|flags;low_delay")

threat_model = YOLO("pipeline/models/weights/best.pt")
person_model = YOLO("pipeline/models/weights/yolov8n.pt")

PERSON_CONFIDENCE_THRESHOLD = float(os.getenv("PERSON_CONFIDENCE_THRESHOLD", "0.25"))
PERSON_NMS_IOU_THRESHOLD = float(os.getenv("PERSON_NMS_IOU_THRESHOLD", "0.70"))
WEAPON_CONFIDENCE_THRESHOLD = float(os.getenv("WEAPON_CONFIDENCE_THRESHOLD", "0.50"))
WEAPON_NMS_IOU_THRESHOLD = float(os.getenv("WEAPON_NMS_IOU_THRESHOLD", "0.50"))
TEMPORAL_CONFIRMATION_FRAMES = int(os.getenv("TEMPORAL_CONFIRMATION_FRAMES", "3"))


# #cache for the camera settings, refresh every 30 seconds ---- still need to test
# _camera_settings: dict =  {
#     "confidence_threshold": 0.5,
#     "zones": []
# }
# _settings_lock = threading.Lock()


load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")




BACKEND_URL = os.getenv("BACKEND_URL", "https://api.neighbourhoodwatchdog.co.za")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-token")
MEDIAMTX_RTSP_URL = os.getenv("MEDIAMTX_RTSP_URL", "rtsp://stream.neighbourhoodwatchdog.co.za:8554")

_model_lock = threading.Lock()

#clip recording settings
WEAPON_CLASSES = {"gun", "knife", "grenade", "explosion"}
CLIP_COOLDOWN_SECS = 0
CLIP_RETENTION_DAYS = int(os.getenv("CLIP_RETENTION_DAYS", "7"))
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")

def _s3_client(): 
    return boto3.client("s3", region_name=AWS_REGION)




#cooldown tracker per weapon class
_clips_cooldowns: dict[tuple[str, str], float] = {}
_cooldown_lock = threading.Lock()


def _push_annotations(backend_url: str, camera_id: str, tracks: list, timestamp: str) -> None:
    """POST detection track data to backend so it can broadcast via WebSocket."""
    api_key = keyring.get_password("WatchDog", "api_key")
    if not api_key:
        logger.warning("Cannot push annotations for camera %s: no paired API key found. Run agent pairing first.", camera_id)
        return


    try:
        response = httpx.post(
            f"{backend_url}/api/stream/cameras/{camera_id}/annotations",
            headers={"X-Internal-Token": api_key},
            json={"tracks": tracks, "timestamp": timestamp},
            timeout=0.5,
        )
        response.raise_for_status()
    except httpx.RequestError as error:
        logger.warning("Could not push annotations for camera %s: %s", camera_id, error)


def _extract_detections(frame, zones: list | tuple | None = None, confidence_threshold: float | None = None) -> tuple[list, list]:
    """Convert YOLO results to DeepSort detection format.
    
    runs both models and retains their detection inside the configured camera zones
    
    no zones = all detection are retained
    configured zones = detections are retained only when the centre of the boundary box falls inside at least one polygon
    """

    zones = zones or []


    person_confidence = (PERSON_CONFIDENCE_THRESHOLD if confidence_threshold is None else confidence_threshold)
    weapon_confidence = WEAPON_CONFIDENCE_THRESHOLD

    # #running yolo on frame, applying the confidendce threshold and zone filters
    # with _settings_lock:
    #     threshold = _camera_settings["confidence_threshold"]
    #     zones = list(_camera_settings["zones"])



    frame_h, frame_w = frame.shape[:2]

    #only passing human objects to deepsort
    person_detections = []
    weapon_detections = []


    with _model_lock:

        #threat detection
        threat_results = threat_model.predict(
            frame,
            imgsz=512,
            conf=weapon_confidence,
            iou=WEAPON_NMS_IOU_THRESHOLD,
            verbose=False
        )


        #person detection
        person_results = person_model.predict(
            frame,
            imgsz=640,
            conf=person_confidence,
            iou=PERSON_NMS_IOU_THRESHOLD,
            classes=[0],
            verbose=False
            )

    for box in threat_results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        confidence = float(box.conf[0])

        label = threat_model.names[int(box.cls[0])] # represents gun, knife, grenade

        weapon_detections.append(([x1, y1, x2 - x1, y2 - y1], confidence, label))


    for box in person_results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        confidence = float(box.conf[0])
        person_detections.append(([x1, y1, x2 - x1, y2 - y1], confidence, "HUMAN_PRESENCE"))



    #applying the zones filter (current plan: pass all it no zones are configured)
    person_detections = filter_detections_by_zones(person_detections, zones, frame_w, frame_h)
    weapon_detections = filter_detections_by_zones(weapon_detections, zones, frame_w, frame_h)




    logger.debug("Filtered detections: persons=%s, threats=%s, zones=%s, threshold=%.2f", len(person_detections), len(weapon_detections), len(zones), confidence_threshold if confidence_threshold is not None else person_confidence)


    return person_detections, weapon_detections


def _build_track_payload(track) -> dict:
    """Convert a confirmed DeepSort track to the annotation payload format."""
    left, top, right, bottom = track.to_ltrb()

    detection_type = track.get_det_class() or "HUMAN_PRESENCE"


    return {
        "track_id": track.track_id,
        "confidence": float(track.det_conf) if track.det_conf is not None else 0.0,
        "bbox": [left, top, right, bottom],
        "detection_type": detection_type,
    }


def _send_new_person_alert(camera: CameraSpec, track_id: int, confidence: float, detection_type: str = "UNKNOWN") -> None:
    """Send a one-time human-presence alert to the backend."""
    try:
        api_key = keyring.get_password("WatchDog", "api_key")

        httpx.post(
            f"{BACKEND_URL}/alerts/",
            json={
                "camera_id": camera.id,
                "neighbourhood_id": camera.neighbourhood_id,
                "detection_type": detection_type.upper(), #GUN, KNIFE, GRENADE
                "confidence": confidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "thumbnail_url": None,
            },
            headers={"X-Internal-Token": api_key},
            timeout=1.0,
        )
    except Exception:
        logger.exception("Alert POST failed for camera %s", camera.id, track_id)


def _open_stream(rtsp_url: str):
    """Open an RTSP stream, returning None if unavailable."""
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        return None

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    return cap

class LatestFrameReader:
    """Retain newest frame. Prevents detector from working through a backlog of old frames"""

    def __init__(self, rtsp_url: str, stop_event: threading.Event):
        self.rtsp_url = rtsp_url
        self.stop_event = stop_event
        self._lock = threading.Lock()
        self._frame = None
        self._sequence = 0

        self._closed = threading.Event()
        self._thread = threading.Thread(target=self._run, name="watchdog-latest-frame-reader", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def get_latest_after(self, previous_sequence: int):
        """returns newer frame"""

        with self._lock:
            if self._frame is None or self._sequence == previous_sequence:
                return None, previous_sequence


            return self._frame, self._sequence


    def close(self) -> None:
        self._closed.set()
        self._thread.join(timeout=2)


    def _run(self) -> None:
        cap = None

        try:
            while not self.stop_event.is_set() and not self._closed.is_set():
                if cap is None or not cap.isOpened():
                    cap = _open_stream(self.rtsp_url)


                    if cap is None:
                        self.stop_event.wait(1)
                        continue


                ok, frame = cap.read()

                if not ok:
                    cap.release()
                    cap = None
                    self.stop_event.wait(0.1)

                    continue

                with self._lock:
                    self._frame = frame
                    self._sequence += 1

        finally:
            if cap is not None:
                cap.release()

def _create_weapon_alert(camera: CameraSpec, weapon_label: str, confidence: float) -> str | None:
    """Create a weapon alert immediately, independently of S3 footage."""

    api_key = keyring.get_password("WatchDog", "api_key") or INTERNAL_API_TOKEN

    payload = {
        "camera_id": camera.id,
        "detection_type": "WEAPON_DETECTED",
        "confidence_score": confidence,
        "frame_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Creating weapon alert: camera=%s, label=%s, confidence=%.3f, backend=%s",
        camera.id,
        weapon_label,
        confidence,
        BACKEND_URL,
    )

    try:
        response = httpx.post(
            f"{BACKEND_URL}/internal/alerts",
            headers={"X-Internal-Token": api_key},
            json=payload,
            timeout=10.0,
        )

        logger.info("Weapon alert API response: status=%s, body=%s", response.status_code, response.text)

        response.raise_for_status()

        alert_id = response.json().get("alert_id")
        if not alert_id:
            raise RuntimeError(
                "Weapon alert API returned 2xx but no alert_id: "
                f"{response.text}"
            )

        logger.info(
            "Created weapon alert %s for camera %s (%s, %.2f)",
            alert_id,
            camera.id,
            weapon_label,
            confidence,
        )


        return str(alert_id)

    except httpx.HTTPStatusError as error:
        logger.error(
            "Weapon alert API rejected request: status=%s, body=%s",
            error.response.status_code,
            error.response.text,
        )
        return None

    except httpx.RequestError as error:
        logger.error(
            "Could not reach weapon alert API at %s: %s",
            BACKEND_URL,
            error,
        )
        return None

    except Exception:
        logger.exception(
            "Unexpected weapon-alert creation failure for camera %s (%s)",
            camera.id,
            weapon_label,
        )
        return None

def _schedule_weapon_clip(camera: CameraSpec, rtsp_url: str, pre_frames: list, weapon_label: str, confidence: float, stop_event: threading.Event) -> None:
    
    label = weapon_label.lower()
    cooldown_key = (camera.id, label)
    now = time.monotonic()

    with _cooldown_lock:
        previous = _clips_cooldowns.get(cooldown_key)

        if previous is not None and now - previous < CLIP_COOLDOWN_SECS:
            logger.info(
                "Weapon alert cooldown active for camera %s / %s",
                camera.id,
                label,
            )
            return

        _clips_cooldowns[cooldown_key] = now

    alert_id = _create_weapon_alert(
        camera=camera,
        weapon_label=label,
        confidence=confidence,
    )

    if alert_id is None:
        with _cooldown_lock:
            if _clips_cooldowns.get(cooldown_key) == now:
                _clips_cooldowns.pop(cooldown_key, None)

        return

    threading.Thread(
        target=_save_weapon_clip,
        args=(
            alert_id,
            camera,
            rtsp_url,
            pre_frames,
            label,
            confidence,
            stop_event,
        ),
        name=f"watchdog-clip-{camera.id}-{label}",
        daemon=True,
    ).start()

    logger.info(
        "Scheduled footage capture for weapon alert %s on camera %s: "
        "label=%s, confidence=%.2f, pre_frames=%s",
        alert_id,
        camera.id,
        label,
        confidence,
        len(pre_frames),
    )

def _save_weapon_clip(alert_id: str, camera: CameraSpec, rtsp_url: str, pre_frames: list, weapon_label: str, confidence: float, stop_event: threading.Event) -> None:
    
    api_key = keyring.get_password("WatchDog", "api_key") or INTERNAL_API_TOKEN
    headers = {"X-Internal-Token": api_key}

    post_frames = []
    capture = _open_stream(rtsp_url)

    try:
        if capture is None:
            logger.warning(
                "Could not capture post-event footage for alert %s / camera %s",
                alert_id,
                camera.id,
            )
        else:
            deadline = time.monotonic() + 3.0

            while time.monotonic() < deadline and not stop_event.is_set():
                ok, frame = capture.read()

                if not ok:
                    break

                post_frames.append(frame)
    finally:
        if capture is not None:
            capture.release()

    all_frames = pre_frames + post_frames

    if not all_frames:
        logger.warning(
            "No frames available for footage of alert %s / camera %s",
            alert_id,
            camera.id,
        )
        return

    height, width = all_frames[0].shape[:2]

    all_frames = [
        frame
        for frame in all_frames
        if frame.shape[:2] == (height, width)
    ]

    if not all_frames:
        logger.warning("No consistently sized frames available for alert %s / camera %s", alert_id, camera.id)
        return

    raw_fd, raw_path = tempfile.mkstemp(suffix=".mp4")
    h264_fd, h264_path = tempfile.mkstemp(suffix=".mp4")

    os.close(raw_fd)
    os.close(h264_fd)

    try:
        writer = cv2.VideoWriter(
            raw_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            25,
            (width, height),
        )

        if not writer.isOpened():
            raise RuntimeError("OpenCV could not initialise the temporary clip writer")

        try:
            for frame in all_frames:
                writer.write(frame)
        finally:
            writer.release()


        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                raw_path,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-movflags",
                "+faststart",
                "-an",
                h264_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        with open(h264_path, "rb") as clip_file:
            upload_response = httpx.post(
                f"{BACKEND_URL}/internal/alerts/{alert_id}/clip",
                headers=headers,
                files={"clip": ("weapon-alert.mp4", clip_file, "video/mp4")},
                timeout=30.0,
            )
        upload_response.raise_for_status()

        logger.info(
            "Clip uploaded through backend and linked to alert %s",
            alert_id,
        )

    except Exception:
        logger.exception("Footage capture/backend upload failed for alert %s / camera %s", alert_id, camera.id)

    finally:
        for clip_path in (raw_path, h264_path):
            if os.path.exists(clip_path):
                os.unlink(clip_path)

def _detection_loop(camera: CameraSpec, rtsp_url: str, stop_event: threading.Event) -> None:
    """
    Background thread: continuously read RTSP, run YOLO+DeepSort, push annotations.
    The frontend uses WebRTC from mediamtx for display; this loop supplies bounding boxes.
    """
    logger.info("Detection loop starting for camera %s at %s", camera.id, rtsp_url)

    tracker = DeepSort(
        max_age=10,
        n_init=TEMPORAL_CONFIRMATION_FRAMES,
        max_iou_distance=0.5,  #for stricter matching and less duplicate boxes
        embedder="mobilenet",
        embedder_gpu=False,
        nms_max_overlap=0.5 #to suppress overlapping boxes
    )

    alerted_ids: set = set()
    pre_event_frames: deque = deque(maxlen=100)
    latest_frame_reader = LatestFrameReader(rtsp_url, stop_event)
    latest_frame_reader.start()
    last_processed_sequence = -1

    try:
        while not stop_event.is_set():
            frame, last_processed_sequence = latest_frame_reader.get_latest_after(last_processed_sequence)

            if frame is None:
                stop_event.wait(0.01)
                continue


            pre_event_frames.append(frame.copy())

            person_detections, weapon_detections = _extract_detections(frame, zones=camera.zones, confidence_threshold=camera.confidence_threshold)

            #only tracking humans through deepsort
            tracks = tracker.update_tracks(person_detections, frame=frame)

            tracks_payload = _collect_tracks(tracks, alerted_ids, camera)

            print(f"DEBUG: raw_tracks={len(tracks)}, confirmed={sum(1 for t in tracks if t.is_confirmed())}, payload={len(tracks_payload)}, person_dets={len(person_detections)}")



            #adding raw weapon detections (no deepsort, no duplication)
            for i, (bbox, confidence, label) in enumerate(weapon_detections):
                x, y, w, h = bbox

                tracks_payload.append({
                    "track_id": f"threat_{i}",
                    "confidence": confidence,
                    "bbox": [x, y, x + w, y + h],
                    "detection_type": label

                })


                if label.lower() in WEAPON_CLASSES:

                    logger.info(
                        "Weapon detection observed: camera=%s, label=%s, confidence=%.3f",
                        camera.id,
                        label,
                        confidence,
                    )
                    
                    _schedule_weapon_clip(
                        camera=camera,
                        rtsp_url=rtsp_url,
                        pre_frames=list(pre_event_frames),
                        weapon_label=label,
                        confidence=confidence,
                        stop_event=stop_event

                    )

            #filtering out zero confidence (0%) ghost tracks
            tracks_payload = [t for t in tracks_payload
                if t.get("confidence", 0) > 0.1 or str(t.get("track_id", "")).startswith("threat_")]


            _push_annotations(BACKEND_URL, camera.id, tracks_payload, datetime.now(timezone.utc).isoformat())

    except Exception:
        logger.exception("Detection worker crashed for camera %s", camera.id)
    finally:
        latest_frame_reader.close()
        logger.info("Detection worker stopped for camera %s", camera.id)

        logger.info("Detection worker stopped for camera %s", camera.id)


def _reconnect_if_needed(cap, rtsp_url: str, stop_event: threading.Event):
    """Return an open capture, reconnecting if necessary."""
    if cap is not None and cap.isOpened():
        return cap
    logger.info("Connecting detection worker to %s", rtsp_url)
    new_cap = _open_stream(rtsp_url)
    if new_cap is None:
        logger.warning("Published stream unavailable - retrying in 5s")
        stop_event.wait(5)
        return None
    logger.info("Published MediaMTX stream connected")
    return new_cap


def _collect_tracks(tracks, alerted_ids: set, camera: CameraSpec) -> list:
    """Build the annotation payload from confirmed tracks, firing alerts for new persons."""
    payload = []
    for track in tracks:
        if not track.is_confirmed() or track.time_since_update > 0:
            continue


        track_id = track.track_id
        track_data = _build_track_payload(track)
        payload.append(track_data)

        if (track.det_conf is not None and is_track_ready_to_alert(track, alerted_ids, TEMPORAL_CONFIRMATION_FRAMES)):
            alerted_ids.add(track_id)

            detection_type = track.get_det_class() or "UNKNOWN"

            logger.info("New detection - Track ID: %s, conf: %.2f", detection_type, camera.id, track_id, track.det_conf)
            _send_new_person_alert(camera, track_id, float(track.det_conf), detection_type)
    return payload


@asynccontextmanager
async def lifespan(app_: FastAPI):
    """Start the detection background thread when the AI service starts."""

    supervisor = CameraSupervisor(
        backend_url=BACKEND_URL,
        internal_token=INTERNAL_API_TOKEN,
        mediamtx_rtsp_url=MEDIAMTX_RTSP_URL,
        detection_target=_detection_loop,
        reconcile_interval_seconds=5.0
    )

    app_.state.camera_supervisor = supervisor
    supervisor.start()

    logger.info("Camera supervisor started")

    try:
        yield
    finally:
        supervisor.stop()
        logger.info("Camera supervisor stopped")



app = FastAPI(
title="WatchDog AI Service",
lifespan=lifespan,
)

stream_router = APIRouter(
    prefix="/stream",
    tags=["stream"],
)

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
                    "detection_type": "HUMAN_PRESENCE",

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
