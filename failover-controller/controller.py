from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import asyncio
import logging
import os
import signal
import subprocess
import httpx


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

logger = logging.getLogger("watchdog.failover")



BACKEND_URL = os.environ["BACKEND_URL"].rstrip("/")
FAILOVER_CONTROLLER_TOKEN = os.environ["FAILOVER_CONTROLLER_TOKEN"]
GO2RTC_URL = os.getenv("GO2RTC_URL", "http://go2rtc:1984").rstrip("/")
GO2RTC_USERNAME = os.environ["GO2RTC_API_USERNAME"]
GO2RTC_PASSWORD = os.environ["GO2RTC_API_PASSWORD"]
MEDIAMTX_API_URL = os.getenv("MEDIAMTX_API_URL", "http://mediamtx:9997").rstrip("/")
MEDIAMTX_RTSP_URL = os.getenv("MEDIAMTX_RTSP_URL", "rtsp://mediamtx:8554").rstrip("/")
GO2RTC_RTSP_URL = os.getenv("GO2RTC_RTSP_URL", "rtsp://go2rtc:8554").rstrip("/")
POLL_SECONDS = float(os.getenv("FAILOVER_POLL_SECONDS", "5"))
FAILURE_PROBES = int(os.getenv("FAILOVER_FAILURE_PROBES", "3"))
BACKUP_HOLD_SECONDS = float(os.getenv("FAILOVER_BACKUP_HOLD_SECONDS", "30"))


@dataclass(frozen=True)
class Camera:
    id: str
    rtsp_url: str
    publish_username: str
    publish_password: str


@dataclass(frozen=True)
class PathStatus:
    source_id: str | None
    online: bool


@dataclass
class Runtime:
    camera: Camera
    state: str = "EDGE_ACTIVE"
    failure_probes: int = 0
    backup_started_at: float | None = None
    go2rtc_stream_name: str | None = None
    backup_source_id: str | None = None
    ffmpeg_process: subprocess.Popen[bytes] | None = None


class FailoverController:
    def __init__(self) -> None:

        self.runtimes: dict[str, Runtime] = {}
        self.stop_event = asyncio.Event()
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(8.0))

    async def run(self) -> None:
        logger.info("Failover controller started")
        try:
            while not self.stop_event.is_set():
                try:
                    await self.reconcile_once()
                except Exception:
                    logger.exception("Failover reconciliation failed")
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=POLL_SECONDS)
                except asyncio.TimeoutError:
                    pass
        finally:
            await self.stop_all_backups()
            await self.client.aclose()


            logger.info("Failover controller stopped")

    async def reconcile_once(self) -> None:

        cameras = await self.fetch_cameras()
        paths = await self.fetch_paths()
        desired_ids = {camera.id for camera in cameras}

        for camera_id in set(self.runtimes) - desired_ids:
            await self.stop_backup(self.runtimes[camera_id], next_state="EDGE_ACTIVE")

            self.runtimes.pop(camera_id, None)

        for camera in cameras:
            runtime = self.runtimes.get(camera.id)
            if runtime is None:
                runtime = Runtime(camera=camera)

                self.runtimes[camera.id] = runtime
            else:
                runtime.camera = camera

            await self.reconcile_camera(runtime, paths.get(camera.id, PathStatus(source_id=None, online=False)))

    async def fetch_cameras(self) -> list[Camera]:
        response = await self.client.get(
            f"{BACKEND_URL}/internal/failover/cameras",
            headers={"X-Failover-Token": FAILOVER_CONTROLLER_TOKEN}
        )

        response.raise_for_status()
        payload = response.json()

        return [
            Camera(
                id=str(item["id"]),
                rtsp_url=str(item["rtsp_url"]),
                publish_username=str(item["publish_username"]),
                publish_password=str(item["publish_password"])
            )

            for item in payload.get("data", [])


        ]

    async def fetch_paths(self) -> dict[str, PathStatus]:
        response = await self.client.get(f"{MEDIAMTX_API_URL}/v3/paths/list")
        response.raise_for_status()
        payload = response.json()

        result: dict[str, PathStatus] = {}

        for item in payload.get("items", []):
            name = str(item.get("name", ""))
            if not name.startswith("cameras/"):
                continue

            camera_id = name.removeprefix("cameras/")
            source = item.get("source") or {}
            source_id = source.get("id") if isinstance(source, dict) else None
            online = bool(item.get("online", item.get("ready", False)))


            result[camera_id] = PathStatus(
                source_id=str(source_id) if source_id else None,
                online=online
            )


        return result

    async def reconcile_camera(self, runtime: Runtime, path: PathStatus) -> None:
        if runtime.state == "EDGE_ACTIVE":
            if path.online:
                runtime.failure_probes = 0

                return

            runtime.failure_probes += 1


            logger.warning(
                "Camera %s has no live MediaMTX publisher (%s/%s failed probes)",
                runtime.camera.id,
                runtime.failure_probes,
                FAILURE_PROBES
            )


            if runtime.failure_probes >= FAILURE_PROBES:
                await self.start_backup(runtime)




            return

        if runtime.state == "BACKUP_ACTIVE":
            #mdiaMTX exposes a unique source.id for the active publisher.
            #with the overridePublisher enabled, a returning Edge Agent replaces the backup source. A changed source ID is therefore our recovery signal and does not require changing the Edge Agent yet.
         
            if (runtime.backup_source_id is not None and path.source_id is not None and path.source_id != runtime.backup_source_id):

                logger.info("Edge publisher reclaimed camera %s; stopping backup", runtime.camera.id)

                await self.stop_backup(runtime, next_state="EDGE_ACTIVE")



                return

            if runtime.backup_source_id is None and path.online and path.source_id:
                runtime.backup_source_id = path.source_id

                logger.info("Registered backup MediaMTX source %s for camera %s", path.source_id, runtime.camera.id)



            if runtime.ffmpeg_process is None or runtime.ffmpeg_process.poll() is not None:
                logger.warning("Backup publisher exited for camera %s", runtime.camera.id)


                await self.stop_backup(runtime, next_state="EDGE_ACTIVE")

                runtime.failure_probes = FAILURE_PROBES



                return

            #  keep the backup active for a minimum period to avoid rapid source flapping. No AI process is started here.
            return

    async def start_backup(self, runtime: Runtime) -> None:
        camera = runtime.camera

        if runtime.ffmpeg_process is not None and runtime.ffmpeg_process.poll() is None:
            return

        stream_name = f"backup-{camera.id}"
        await self.configure_go2rtc_stream(stream_name, camera.rtsp_url)

        source_url = f"{GO2RTC_RTSP_URL}/{stream_name}"

        target_url = self.authenticated_mediamtx_publish_url(camera)
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-nostdin",
            "-rtsp_transport",
            "tcp",
            "-i",
            source_url,
            "-map",
            "0:v:0",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-pix_fmt",
            "yuv420p",
            "-g",
            "30",
            "-keyint_min",
            "30",
            "-sc_threshold",
            "0",
            "-f",
            "rtsp",
            "-rtsp_transport",
            "tcp",
            target_url

            
        ]

        logger.info("Starting Go2RTC backup for camera %s", camera.id)

        
        runtime.ffmpeg_process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )


        runtime.go2rtc_stream_name = stream_name
        runtime.backup_started_at = asyncio.get_running_loop().time()
        runtime.backup_source_id = None
        runtime.failure_probes = 0
        runtime.state = "BACKUP_ACTIVE"
        logger.info("Camera %s is now BACKUP_ACTIVE", camera.id)

    async def stop_backup(self, runtime: Runtime, *, next_state: str) -> None:
        process = runtime.ffmpeg_process

        if process is not None and process.poll() is None:
            logger.info("Stopping backup publisher for camera %s", runtime.camera.id)
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=8)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        runtime.ffmpeg_process = None
        if runtime.go2rtc_stream_name:
            await self.delete_go2rtc_stream(runtime.go2rtc_stream_name)
        runtime.go2rtc_stream_name = None
        runtime.backup_started_at = None
        runtime.backup_source_id = None
        runtime.failure_probes = 0
        runtime.state = next_state


        logger.info("Camera %s is now %s", runtime.camera.id, next_state)

    async def stop_all_backups(self) -> None:

        for runtime in list(self.runtimes.values()):
            if runtime.state == "BACKUP_ACTIVE":
                await self.stop_backup(runtime, next_state="EDGE_ACTIVE")

    async def configure_go2rtc_stream(self, name: str, source_url: str) -> None:

        response = await self.client.put(

            f"{GO2RTC_URL}/api/streams",
            params={"name": name, "src": source_url},
            auth=(GO2RTC_USERNAME, GO2RTC_PASSWORD)
        )


        response.raise_for_status()

    async def delete_go2rtc_stream(self, name: str) -> None:

        response = await self.client.delete(
            f"{GO2RTC_URL}/api/streams",
            params={"src": name},
            auth=(GO2RTC_USERNAME, GO2RTC_PASSWORD)
        )


        if response.status_code not in {200, 204, 404}:
            response.raise_for_status()


    def authenticated_mediamtx_publish_url(self, camera: Camera) -> str:

        scheme, authority = MEDIAMTX_RTSP_URL.split("://", 1)
        username = quote(camera.publish_username, safe="")
        password = quote(camera.publish_password, safe="")

        
        return f"{scheme}://{username}:{password}@{authority}/cameras/{camera.id}"


def main() -> None:
    controller = FailoverController()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for signal_number in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(signal_number, controller.stop_event.set)

    try:
        loop.run_until_complete(controller.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()