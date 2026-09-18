from camera_runtime import CameraSpec, CameraSupervisor

import os
import cv2
import time
import threading
import tempfile
import subprocess
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from pipeline.utils.thumbnail import annotate_frame, encode_frame_as_jpeg
from pipeline.utils.frame_buffer import AnnotatedFrameBuffer
from pipeline.processing.cascaded_pipeline import CascadedPipeline, CascadedPipelineConfig

import httpx
import logging
import keyring
import boto3
from runtime.paths import get_resource_dir

RESOURCE_DIR = get_resource_dir()

logger = logging.getLogger("watchdog.ai")
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = ("rtsp_transport;tcp|fflags;nobuffer|flags;low_delay")

THREAT_MODEL_PATH = (
    RESOURCE_DIR
    / "pipeline"
    / "models"
    / "weights"
    / "best.pt"
)

PERSON_MODEL_PATH = (
    RESOURCE_DIR
    / "pipeline"
    / "models"
    / "weights"
    / "yolov8n.pt"
)

threat_model = YOLO(str(THREAT_MODEL_PATH))
person_model = YOLO(str(PERSON_MODEL_PATH))

PERSON_CONFIDENCE_THRESHOLD = float(os.getenv("PERSON_CONFIDENCE_THRESHOLD", "0.25"))
PERSON_NMS_IOU_THRESHOLD = float(os.getenv("PERSON_NMS_IOU_THRESHOLD", "0.70"))
WEAPON_CONFIDENCE_THRESHOLD = float(os.getenv("WEAPON_CONFIDENCE_THRESHOLD", "0.50"))
WEAPON_NMS_IOU_THRESHOLD = float(os.getenv("WEAPON_NMS_IOU_THRESHOLD", "0.50"))
TEMPORAL_CONFIRMATION_FRAMES = int(os.getenv("TEMPORAL_CONFIRMATION_FRAMES", "3"))

APPEARANCE_EMBEDDING_MODEL = "deep_sort_mobilenet_v2_bottleneck"

# #cache for the camera settings, refresh every 30 seconds ---- still need to test
# _camera_settings: dict =  {
#     "confidence_threshold": 0.5,
#     "zones": []
# }
# _settings_lock = threading.Lock()


load_dotenv(RESOURCE_DIR / ".env")




BACKEND_URL = os.getenv("BACKEND_URL", "https://api.neighbourhoodwatchdog.co.za")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-token")
MEDIAMTX_RTSP_URL = os.getenv("MEDIAMTX_RTSP_URL", "rtsp://stream.neighbourhoodwatchdog.co.za:8554")

_model_lock = threading.Lock()

#clip recording settings
WEAPON_CLASSES = {"gun", "knife", "grenade", "explosion"}
CLIP_COOLDOWN_SECS = 5
CLIP_RETENTION_DAYS = int(os.getenv("CLIP_RETENTION_DAYS", "7"))
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "af-south-1")

def _s3_client(): 
    return boto3.client("s3", region_name=AWS_REGION)




#cooldown tracker per weapon class
_clips_cooldowns: dict[tuple[str, int, str], float] = {}
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


def _post_detection_event(camera: CameraSpec, event: dict) -> None:
    """ send one edge-triggered classified event to the backend."""

    api_key = keyring.get_password("WatchDog", "api_key")
    if not api_key:
        logger.warning("Cannot post detection event for camera %s: no paired API key", camera.id)
        return

    payload = {
        "camera_id": camera.id,
        "frame_timestamp": datetime.now(timezone.utc).isoformat(),
        "detection_type": event["detection_type"],
        "confidence_score": float(event["confidence"]),
        "zone_id": event.get("zone_id")
    }

    try:
        response = httpx.post(
            f"{BACKEND_URL}/internal/detections",
            headers={"X-Internal-Token": api_key},
            json=payload,
            timeout=1.0
        )

        response.raise_for_status()

    except httpx.RequestError as error:
        logger.warning(
            "Could not post detection event for camera %s: %s", camera.id, error)
    except httpx.HTTPStatusError as error:
        logger.warning("Backend rejected detection event for camera %s: %s", camera.id, error.response.status_code)





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


def _match_tracking_subject(camera: CameraSpec, appearance_embedding: list[float], api_key: str) -> tuple[bool, str | None, float | None]:
    """
    Attempt to match an appearance embedding against an active tracking subject (does this person look like an existing tracking subject)

    Returns: (request_succeeded, tracking_subject_id, similarity)
    A successful request with no match returns: (True, None, None)
    A failed matcher request returns: (False, None, None)
    """

    try:
        response = httpx.post(
            f"{BACKEND_URL}/internal/tracking/match",
            headers={"X-Internal-Token": api_key},
    
            json={
                "camera_id": camera.id,
                "appearance_embedding": appearance_embedding,
                "embedding_model": APPEARANCE_EMBEDDING_MODEL
    
            },
            timeout=10.0
    
        )
    
        response.raise_for_status()
        response_data = response.json()
        match_data = response_data.get("data") or {}
    
        if not match_data.get("matched"):
            logger.info("No existing tracking subject matched camera=%s", camera.id)
    
            return True, None, None
    
        tracking_subject_id = match_data.get("tracking_subject_id")
        similarity = match_data.get("similarity")
    
        if not tracking_subject_id or similarity is None:
            raise RuntimeError("Tracking matcher returned matched=true without tracking_subject_id or similarity")
    
        similarity = float(similarity)
    
        logger.info(
            "Tracking subject matched: camera=%s subject=%s similarity=%.4f",
            camera.id,
            tracking_subject_id,
            similarity
    
        )
    
        return True, str(tracking_subject_id), similarity

    
    except httpx.RequestError as error:
        logger.exception(
            "Could not reach tracking matcher for camera=%s: %s",
            camera.id,
            error,
        )
        return False, None, None

    except Exception:
        logger.exception(
            "Unexpected tracking matcher failure for camera=%s",
            camera.id,
        )
        return False, None, None



def _record_tracking_sighting(camera: CameraSpec, local_track_id: int, observed_at: str, tracking_subject_id: str, match_confidence: float, api_key: str) -> str | None:
    """
    Persist a validated cross-camera sighting.

    Returns the parent alert ID so the clip remains attached to the original incident.

    inform backend that existing subject was seen on camera
    """

    try:
        response = httpx.post(
            f"{BACKEND_URL}/internal/tracking/sightings",
            headers={"X-Internal-Token": api_key},

            json={
                "tracking_subject_id": tracking_subject_id,
                "camera_id": camera.id,
                "local_track_id": local_track_id,
                "observed_at": observed_at,
                "match_confidence": match_confidence

            },
            timeout=10.0

        )

        response.raise_for_status()

        response_data = response.json()
        sighting_data = response_data.get("data") or {}
        alert_id = sighting_data.get("alert_id")

        if not alert_id:
            raise RuntimeError("Tracking sighting endpoint returned 2xx without alert_id")

        logger.info(
            "Recorded tracking sighting: alert=%s subject=%s camera=%s "
            "confidence=%.4f",
            alert_id,
            tracking_subject_id,
            camera.id,
            match_confidence

        )

        return str(alert_id)

    except httpx.HTTPStatusError as error:
        logger.exception(
            "Tracking sighting rejected: camera=%s subject=%s "
            "status=%s body=%s",
            camera.id,
            tracking_subject_id,
            error.response.status_code,
            error.response.text
            
        )
        return None

    except httpx.RequestError as error:
        logger.exception(
            "Could not record tracking sighting for camera=%s subject=%s: %s",
            camera.id,
            tracking_subject_id,
            error

        )
        return None

    except Exception:
        logger.exception(
            "Unexpected tracking sighting failure for camera=%s subject=%s",
            camera.id,
            tracking_subject_id

        )
        return None


def _create_weapon_alert(camera: CameraSpec, weapon_label: str, confidence: float, local_track_id: int, appearance_embedding: list[float] | None = None) -> str | None:
    """
    Match a detection to an existing incident before creating a new alert.

    If a match is found, record a sighting against the existing alert.
    If no match is found, create a new alert and tracking subject.
    """

    api_key = keyring.get_password("WatchDog", "api_key") or INTERNAL_API_TOKEN
    observed_at = datetime.now(timezone.utc).isoformat()

    if appearance_embedding is not None:
        matcher_succeeded, tracking_subject_id, similarity = (
            _match_tracking_subject(camera=camera, appearance_embedding=appearance_embedding, api_key=api_key)
        )


        if tracking_subject_id is not None and similarity is not None:
            #not creating a second alert when the detection matches an existing subject. 
            ## if recording fails, return None instead of creating a duplicate incident.
            return _record_tracking_sighting(
                camera=camera,
                local_track_id=local_track_id,
                observed_at=observed_at,
                tracking_subject_id=tracking_subject_id,
                match_confidence=similarity,
                api_key=api_key

            )

        if not matcher_succeeded:
            logger.warning(
                "Tracking matcher unavailable for camera=%s; "
                "falling back to a new alert",
                camera.id

            )

    payload = {
        "camera_id": camera.id,
        "detection_type": "WEAPON_DETECTED",
        "confidence_score": confidence,
        "local_track_id": local_track_id,
        "frame_timestamp": observed_at,
        "appearance_embedding": appearance_embedding,

        "embedding_model": (
            APPEARANCE_EMBEDDING_MODEL
            if appearance_embedding is not None
            else None
        )

    }

    logger.info(
        "Creating weapon alert: camera=%s, label=%s, confidence=%.3f, "
        "backend=%s",
        camera.id,
        weapon_label,
        confidence,
        BACKEND_URL

    )

    try:
        response = httpx.post(
            f"{BACKEND_URL}/internal/alerts",
            headers={"X-Internal-Token": api_key},
            json=payload,
            timeout=10.0

        )

        logger.info(
            "Weapon alert API response: status=%s, body=%s",
            response.status_code,
            response.text

        )

        response.raise_for_status()

        alert_id = response.json().get("alert_id")

        if not alert_id:
            raise RuntimeError(f"Weapon alert API returned 2xx but no alert_id: {response.text}")

        logger.info(
            "Created weapon alert %s for camera %s (%s, %.2f)",
            alert_id,
            camera.id,
            weapon_label,
            confidence

        )
        

        return str(alert_id)

    except httpx.HTTPStatusError as error:
        logger.exception(
            "Weapon alert API rejected request: status=%s, body=%s",
            error.response.status_code,
            error.response.text

        )
        return None

    except httpx.RequestError as error:
        logger.exception(
            "Could not reach weapon alert API at %s: %s",
            BACKEND_URL,
            error

        )
        return None

    except Exception:
        logger.exception(
            "Unexpected weapon-alert creation failure for camera %s (%s)",
            camera.id,
            weapon_label
        )
        return None
    

def _schedule_weapon_clip(camera: CameraSpec, frame_buffer: AnnotatedFrameBuffer, trigger_sequence: int, weapon_label: str, 
                          confidence: float, local_track_id: int, stop_event: threading.Event, appearance_embedding: list[float] | None = None) -> None:
    
    label = weapon_label.lower()
    cooldown_key = (camera.id, local_track_id, label)
    now = time.monotonic()

    with _cooldown_lock:
        previous = _clips_cooldowns.get(cooldown_key)

        if previous is not None and now - previous < CLIP_COOLDOWN_SECS:
            logger.info(
                "Weapon alert cooldown active for camera %s / %s",
                camera.id,
                label
            )

            return

        _clips_cooldowns[cooldown_key] = now

    alert_id = _create_weapon_alert(
        camera=camera,
        weapon_label=label,
        confidence=confidence,
        local_track_id=local_track_id,
        appearance_embedding=appearance_embedding


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
            frame_buffer,
            trigger_sequence,
            stop_event
        ),
        name=f"watchdog-clip-{camera.id}-{label}",
        daemon=True


    ).start()


    logger.info(
        "Scheduled annotated footage capture for weapon alert %s on camera %s: "
        "label=%s, confidence=%.2f, trigger_sequence=%s",
        alert_id,
        camera.id,
        label,
        confidence,
        trigger_sequence
        
    )

def _save_weapon_clip(alert_id: str, camera: CameraSpec, frame_buffer: AnnotatedFrameBuffer, trigger_sequence: int, stop_event: threading.Event) -> None:
    """
    Build a clip from frames already annotated by the detection loop.

    No YOLO, DeepSort, or second RTSP capture is used here.
    """

    api_key = keyring.get_password("WatchDog", "api_key") or INTERNAL_API_TOKEN
    headers = {"X-Internal-Token": api_key}

    pre_frames = frame_buffer.snapshot_through(trigger_sequence)
    post_frames: list = []

    next_sequence = trigger_sequence
    deadline = time.monotonic() + 3.0

    while time.monotonic() < deadline and not stop_event.is_set():
        new_frames, next_sequence = frame_buffer.wait_for_after(
            next_sequence,
            deadline
        )

        if not new_frames:
            break

        post_frames.extend(new_frames)

    all_frames = pre_frames + post_frames

    if not all_frames:
        logger.warning(
            "No annotated frames available for footage of alert %s / camera %s",
            alert_id,
            camera.id
        )
        return

    height, width = all_frames[0].shape[:2]

    all_frames = [
        frame
        for frame in all_frames
        if frame.shape[:2] == (height, width)
    ]

    if not all_frames:
        logger.warning(
            "No consistently sized frames available for alert %s / camera %s",
            alert_id,
            camera.id
        )
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
            raise RuntimeError(
                "OpenCV could not initialise the temporary clip writer"
            )

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
                files={
                    "clip": (
                        "weapon-alert.mp4",
                        clip_file,
                        "video/mp4"
                    )
                },
                timeout=30.0
            )


        upload_response.raise_for_status()

        logger.info("Annotated clip uploaded through backend and linked to alert %s", alert_id)

    except Exception:
        logger.exception(
            "Annotated footage capture/backend upload failed "
            "for alert %s / camera %s",
            alert_id,
            camera.id 
            
        )

    finally:
        for clip_path in (raw_path, h264_path):
            if os.path.exists(clip_path):
                os.unlink(clip_path)

def _detection_loop(camera: CameraSpec, rtsp_url: str, stop_event: threading.Event) -> None:
    """"reads one camera, runs the cascaded pipeline, and publish results."""

    logger.info("Detection loop starting for camera %s", camera.id)

    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=threat_model,
        zones=camera.zones,
        zone_ids=camera.zone_ids,

        config=CascadedPipelineConfig(
            person_confidence=camera.confidence_threshold,
            person_iou=PERSON_NMS_IOU_THRESHOLD,
            weapon_confidence=WEAPON_CONFIDENCE_THRESHOLD,
            weapon_iou=WEAPON_NMS_IOU_THRESHOLD,
            n_init=TEMPORAL_CONFIRMATION_FRAMES,
            loitering_threshold_seconds=float(
                os.getenv("LOITERING_THRESHOLD_SECONDS", "30")
            ),
            scan_time_window_seconds=float(
                os.getenv("SCAN_TIME_WINDOW_SECONDS", "30")
            ),
            scan_crossing_threshold=int(
                os.getenv("SCAN_CROSSING_THRESHOLD", "3")
            )
        ),

        inference_lock=_model_lock


    )

    annotated_frames = AnnotatedFrameBuffer(max_frames=100)
    latest_frame_reader = LatestFrameReader(rtsp_url, stop_event)
    latest_frame_reader.start()
    last_processed_sequence = -1

    try:
        while not stop_event.is_set():
            frame, last_processed_sequence = latest_frame_reader.get_latest_after(last_processed_sequence)

            if frame is None:
                stop_event.wait(0.01)
                continue

            result = pipeline.process_frame(frame)
            tracks_payload = result.tracks

            trigger_sequence = annotated_frames.append(annotate_frame(frame, tracks_payload))

            _push_annotations(
                BACKEND_URL,
                camera.id,
                tracks_payload,
                datetime.now(timezone.utc).isoformat()


            )

            for event in result.events:
                _post_detection_event(camera, event)


                if event["detection_type"] == "WEAPON_DETECTED":
                    local_track_id = int(event["track_id"])

                    appearance_embedding = result.appearance_embeddings.get(local_track_id)

                    _schedule_weapon_clip(
                        camera=camera,
                        frame_buffer=annotated_frames,
                        trigger_sequence=trigger_sequence,
                        weapon_label=event.get("weapon_type") or "weapon",
                        confidence=float(event["weapon_confidence"] or event["confidence"]),
                        local_track_id=local_track_id, 
                        stop_event=stop_event,
                        appearance_embedding=appearance_embedding
                        
                    )

    except Exception:
        logger.exception("Detection worker crashed for camera %s", camera.id)
    finally:
        latest_frame_reader.close()
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

    cap = cv2.VideoCapture(
        rtsp_url,
        cv2.CAP_FFMPEG
    )

    if not cap.isOpened():
        return

    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=threat_model,

        config=CascadedPipelineConfig(
            person_confidence=PERSON_CONFIDENCE_THRESHOLD,
            weapon_confidence=WEAPON_CONFIDENCE_THRESHOLD,
        ),

        inference_lock=_model_lock

    )

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            result = pipeline.process_frame(frame)
            annotated = annotate_frame(frame, result.tracks)
            jpeg_bytes = encode_frame_as_jpeg(annotated)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg_bytes
                + b"\r\n"
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

@app.get("/internal/camera-status")
def camera_status():
    supervisor = getattr(app.state, "camera_supervisor", None)

    if supervisor is None:
        return {"cameras": []}

    return {"cameras": supervisor.get_status_snapshot()}
