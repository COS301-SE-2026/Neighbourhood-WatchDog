from __future__ import annotations

import logging
import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import quote

import httpx
import keyring


logger = logging.getLogger("watchdog.ai.runtime")


@dataclass(frozen=True)
class CameraSpec:
    id: str
    rtsp_url: str
    publish_username: str
    publish_password: str
    neighbourhood_id: str | None = None
    confidence_threshold: float = 0.5


@dataclass
class CameraRuntime:
    spec: CameraSpec
    stop_event: threading.Event = field(default_factory=threading.Event)
    ffmpeg_process: subprocess.Popen | None = None
    detection_thread: threading.Thread | None = None
    next_restart_at: float = 0.0
    consecutive_failures: int = 0


DetectionTarget = Callable[[CameraSpec, str, threading.Event], None]


class CameraSupervisor:

    def __init__(self, *, backend_url: str, internal_token: str, mediamtx_rtsp_url: str, detection_target: DetectionTarget, reconcile_interval_seconds: float = 5.0) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.internal_token = internal_token
        self.mediamtx_rtsp_url = mediamtx_rtsp_url.rstrip("/")
        self.detection_target = detection_target
        self.reconcile_interval_seconds = reconcile_interval_seconds

        self._runtimes: dict[str, CameraRuntime] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._reconcile_loop,
            name="watchdog-camera-reconciler",
            daemon=True,
        )
        self._thread.start()
        logger.info("Camera reconciliation loop started")

    def stop(self) -> None:
        logger.info("Stopping camera supervisor")
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=10)

        with self._lock:
            runtimes = list(self._runtimes.values())
            self._runtimes.clear()

        for runtime in runtimes:
            self._stop_runtime(runtime)

        logger.info("Camera supervisor stopped")

    def _reconcile_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                desired_cameras = self._fetch_enabled_cameras()
                self._reconcile(desired_cameras)
            except Exception:
                logger.exception("Camera reconciliation cycle failed")

            self._stop_event.wait(self.reconcile_interval_seconds)

    def _fetch_enabled_cameras(self) -> dict[str, CameraSpec]:
        print("Fetching cameras from: ", self.backend_url)

        api_key = keyring.get_password("WatchDog", "api_key")

        if not api_key:
            raise RuntimeError("No paired API key found in keyring. Run agent pairing before starting the agent.")

        response = httpx.get(
            f"{self.backend_url}/internal/cameras/enabled",
            headers={"X-Internal-Token": api_key},
            timeout=5.0,
        )
        response.raise_for_status()

        payload = response.json()
        cameras = payload.get("data", [])

        result: dict[str, CameraSpec] = {}
        for camera in cameras:
            camera_id = str(camera["id"])
            result[camera_id] = CameraSpec(
                id=camera_id,
                rtsp_url=str(camera["rtsp_url"]),
                publish_username=str(camera["publish_username"]), 
                publish_password=str(camera["publish_password"]),
                neighbourhood_id=(
                    str(camera["neighbourhood_id"])
                    if camera.get("neighbourhood_id")
                    else None
                ),
                confidence_threshold=float(
                    camera.get("confidence_threshold", 0.5)
                ),
            )

        return result

    def _reconcile(self, desired: dict[str, CameraSpec]) -> None:
        with self._lock:
            current_ids = set(self._runtimes)
            desired_ids = set(desired)

            removed_ids = current_ids - desired_ids
            changed_ids = {
                camera_id
                for camera_id in current_ids & desired_ids
                if self._runtimes[camera_id].spec != desired[camera_id]
            }

            removed_runtimes = [
                self._runtimes.pop(camera_id)
                for camera_id in removed_ids | changed_ids
            ]

        for runtime in removed_runtimes:
            logger.info("Stopping disabled or changed camera %s", runtime.spec.id)
            self._stop_runtime(runtime)

        for camera_id, spec in desired.items():
            with self._lock:
                runtime = self._runtimes.get(camera_id)

                if runtime is None:
                    runtime = CameraRuntime(spec=spec)
                    self._runtimes[camera_id] = runtime
                    logger.info("Registering enabled camera %s", camera_id)

            self._ensure_runtime_is_running(runtime)

    def _ensure_runtime_is_running(self, runtime: CameraRuntime) -> None:
        if runtime.stop_event.is_set():
            return

        now = time.monotonic()

        process = runtime.ffmpeg_process
        if process is None or process.poll() is not None:
            if now >= runtime.next_restart_at:
                self._start_ffmpeg(runtime)

        thread = runtime.detection_thread
        if thread is None or not thread.is_alive():
            self._start_detection_thread(runtime)

    def _start_ffmpeg(self, runtime: CameraRuntime) -> None:
        camera_id = runtime.spec.id
        published_url = self._published_rtsp_url(camera_id)

        publisher_url = self._authenticated_publish_rtsp_url(runtime.spec)

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-nostdin",
            "-rtsp_transport",
            "tcp",
            "-i",
            runtime.spec.rtsp_url,
            "-map",
            "0",
            "-c",
            "copy",
            "-f",
            "rtsp",
            "-rtsp_transport",
            "tcp",
            publisher_url,
        ]

        try:
            popen_options: dict = {
                "stdin": subprocess.DEVNULL,
            }

            if os.name == "nt":
                popen_options["creationflags"] = (
                    subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                popen_options["start_new_session"] = True

            runtime.ffmpeg_process = subprocess.Popen(
                command,
                **popen_options,
            )

            # FFmpeg started successfully, so previous retry failures no
            # longer apply to this camera.
            runtime.consecutive_failures = 0
            runtime.next_restart_at = 0.0

            logger.info(
                "Started FFmpeg publisher for camera %s → %s",
                camera_id,
                published_url,
            )
        except OSError:
            runtime.ffmpeg_process = None
            runtime.consecutive_failures += 1
            delay = min(2 ** runtime.consecutive_failures, 30)
            runtime.next_restart_at = time.monotonic() + delay

            logger.exception(
                "Could not start FFmpeg for camera %s; retrying in %ss",
                camera_id,
                delay,
            )

    def _start_detection_thread(self, runtime: CameraRuntime) -> None:
        published_url = self._published_rtsp_url(runtime.spec.id)

        runtime.detection_thread = threading.Thread(
            target=self.detection_target,
            args=(runtime.spec, published_url, runtime.stop_event),
            name=f"watchdog-detection-{runtime.spec.id}",
            daemon=True,
        )
        runtime.detection_thread.start()

        logger.info(
            "Started detection worker for camera %s",
            runtime.spec.id,
        )

    def _stop_runtime(self, runtime: CameraRuntime) -> None:
        runtime.stop_event.set()
        self._terminate_owned_process(runtime.ffmpeg_process)

        if (
            runtime.detection_thread is not None
            and runtime.detection_thread.is_alive()
        ):
            runtime.detection_thread.join(timeout=10)

    @staticmethod
    def _terminate_owned_process(process: subprocess.Popen | None) -> None:
        if process is None or process.poll() is not None:
            return

        try:
            if os.name == "nt":
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(process.pid, signal.SIGTERM)

            process.wait(timeout=8)
            return
        except (OSError, subprocess.TimeoutExpired):
            logger.warning(
                "FFmpeg process %s did not stop gracefully; forcing shutdown",
                process.pid,
            )

        try:
            if os.name == "nt":
                subprocess.run(
                    [
                        "taskkill",
                        "/PID",
                        str(process.pid),
                        "/T",
                        "/F",
                    ],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            logger.exception(
                "Could not force-stop owned FFmpeg process %s",
                process.pid,
            )

    def _published_rtsp_url(self, camera_id: str) -> str:
        return f"{self.mediamtx_rtsp_url}/cameras/{camera_id}"

    def _authenticated_publish_rtsp_url(self, camera: CameraSpec) -> str:

        username = quote(camera.publish_username, safe="")
        password = quote(camera.publish_password, safe="")

        public_url = self._published_rtsp_url(camera.id)

        return public_url.replace("rtsp://", f"rtsp://{username}:{password}@", 1)

    def get_status_snapshot(self) -> list[dict]:
        with self._lock:
            runtimes = list(self._runtimes.values())

        snapshot = []
        for runtime in runtimes:
            process = runtime.ffmpeg_process
            publishing = process is not None and process.poll() is None

            thread = runtime.detection_thread
            detecting = thread is not None and thread.is_alive()

            if publishing and detecting:
                status = "connected"
            elif runtime.consecutive_failures > 0 and not publishing:
                status = "disconnected"
            else:
                status = "checking"

            snapshot.append(
                {
                    "id": runtime.spec.id,
                    "status": status,
                    "publishing": publishing,
                    "detecting": detecting,
                    "consecutive_failures": runtime.consecutive_failures,
                }
            )

        return snapshot