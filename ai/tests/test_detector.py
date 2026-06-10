# pkg_resources compatibility shim
import importlib
import os
import sys
import types

if "pkg_resources" not in sys.modules:
    _mock = types.ModuleType("pkg_resources")
    def _resource_filename(package, path):
        mod = importlib.import_module(package)
        return os.path.join(os.path.dirname(mod.__file__), path)
    _mock.resource_filename = _resource_filename
    sys.modules["pkg_resources"] = _mock

import cv2
import time
import threading
import httpx
from datetime import datetime, timezone
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# configurations
MEDIAMTX_RTSP_URL = "rtsp://localhost:8554/tapo-camera"
BACKEND_URL       = "http://localhost:8000"
CAMERA_ID         = "2"
CONF_THRESHOLD    = 0.4   # lower for more sensitive detection
IOU_THRESHOLD     = 0.3
INFER_SIZE        = 320   # 320 = fast, 640 = accurate

# loaded pre-trained model
model = YOLO("ai/pipeline/models/weights/yolov8n.pt")

tracker = DeepSort(
    max_age=30,            # drop track after 30 frames without detection
    n_init=1,              # confirm track after just 1 detection (show ID immediately)
    max_iou_distance=0.7,
    embedder="mobilenet",
    embedder_gpu=False,
)

# latest-frame reader thread
# this runs continuously and always keeps the MOST RECENT frame in memory.
# the processing loop reads from here such that it's always current, never buffered.

class LatestFrameCapture:
    def __init__(self, url: str):
        self.url = url
        self._frame = None
        self._lock = threading.Lock()
        self._running = True

    def start(self):
        t = threading.Thread(target=self._read_loop, daemon=True)
        t.start()

    def _read_loop(self):
        cap = None
        while self._running:
            if cap is None or not cap.isOpened():
                print("Connecting to RTSP stream…")
                cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not cap.isOpened():
                    print("Failed to connect — retrying in 3s")
                    time.sleep(3)
                    cap = None
                    continue
                print("Stream connected")

            ret, frame = cap.read()
            if ret:
                with self._lock:
                    self._frame = frame
            else:
                print("Frame read failed — reconnecting")
                cap.release()
                cap = None
                time.sleep(1)

    def get(self):
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def stop(self):
        self._running = False


# non-blocking annotation POST
def _post_annotations(tracks: list, timestamp: str):
    try:
        resp = httpx.post(
            f"{BACKEND_URL}/api/stream/cameras/{CAMERA_ID}/annotations",
            json={"tracks": tracks, "timestamp": timestamp},
            timeout=0.5,
        )
        if resp.status_code != 200:
            print(f"Annotation POST failed: {resp.status_code}")
    except Exception as e:
        print(f"Annotation POST error: {e}")


# main detection loop 
def main():
    capture = LatestFrameCapture(MEDIAMTX_RTSP_URL)
    capture.start()

    # wait for first frame
    print("Waiting for first frame…")
    while capture.get() is None:
        time.sleep(0.1)
    print("Stream ready — detection starting")

    unique_ids: set = set()
    alerted_ids: set = set()

    while True:
        frame = capture.get()
        if frame is None:
            time.sleep(0.01)
            continue

        # YOLO detection
        results = model.predict(
            frame,
            verbose=False,
            conf=CONF_THRESHOLD,
            iou=IOU_THRESHOLD,
            imgsz=INFER_SIZE,
            classes=[0],    # persons only
        )

        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            detections.append(([x1, y1, x2 - x1, y2 - y1], conf, "person"))

        # DeepSort tracking
        tracks = tracker.update_tracks(detections, frame=frame)

        tracks_payload = []
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            unique_ids.add(track_id)
            conf = track.det_conf if track.det_conf is not None else 0.0
            left, top, right, bottom = track.to_ltrb()

            print(f"Track ID: {track_id} --- Confidence: {conf:.2f}")

            tracks_payload.append({
                "track_id": track_id,
                "confidence": float(conf),
                "bbox": [left, top, right, bottom],
            })

            # fire alert once per new person
            if track_id not in alerted_ids and conf > 0:
                alerted_ids.add(track_id)
                try:
                    httpx.post(
                        f"{BACKEND_URL}/api/alerts",
                        json={
                            "camera_id": CAMERA_ID,
                            "detection_type": "HUMAN_PRESENCE",
                            "confidence": float(conf),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        timeout=1.0,
                    )
                    print(f"Alert sent for Track ID: {track_id}")
                except Exception as e:
                    print(f"Alert failed: {e}")

        # push annotations to backend
        threading.Thread(
            target=_post_annotations,
            args=(tracks_payload, datetime.now(timezone.utc).isoformat()),
            daemon=True,
        ).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
