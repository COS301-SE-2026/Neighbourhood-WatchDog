from __future__ import annotations

import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger("watchdog.desktop.camera_service")

CONFIGURED = "configured"
CHECKING = "checking"
CONNECTED = "connected"
DISCONNECTED = "disconnected"
UNAVAILABLE = "unavailable"

STATUS_LABELS = {
    CONFIGURED: "Configured",
    CHECKING: "Checking...",
    CONNECTED: "Connected",
    DISCONNECTED: "Disconnected",
    UNAVAILABLE: "Unavailable",
}

@dataclass(frozen=True)
class CameraSummary:
    id: str
    name: str
    location: str | None
    enabled: bool
    status: str = CONFIGURED
    status_reason: str | None = None

    def with_status(self, status: str, reason: str | None) -> "CameraSummary":
        """Returns camera summary with updated status"""
        return CameraSummary(
            id=self.id,
            name=self.name,
            location=self.location,
            enabled=self.enabled,
            status=status,
            status_reason=reason,
        )

    @property
    def display_status(self) -> str:
        return STATUS_LABELS.get(
            self.status,
            self.status.title(),
        )

class CameraService:
    def __init__(
            self, 
            *,
            agent_status_url: str = "http://127.0.0.1:8001/internal/camera-status",
            timeout_seconds: float = 2.0,
            ) -> None:
        self.agent_status_url = agent_status_url
        self.timeout_seconds = timeout_seconds

    def summaries_from_config(self, config_data: dict | None) -> list[CameraSummary]:
        """Builds camera summary list from local config data"""
        config_data = config_data or {}
        cameras = config_data.get("cameras") or []
        summaries: list[CameraSummary] = []

        for camera in cameras:
            if not isinstance(camera, dict):
                continue

            camera_id = camera.get("id")
            if camera_id is None:
                logger.warning(
                    "Skipping a configured camera with no id in persisted config: %r",
                    camera.get("name", "<unnamed>")
                )
                continue

            summaries.append(
                CameraSummary(
                    id=str(camera_id),
                    name=str(camera.get("name") or "Unnamed camera"),
                    location=camera.get("location"),
                    enabled=bool(camera.get("enabled", True)),
                    status=CONFIGURED,
                    status_reason=None,
                )
            )

        return summaries

    def refresh_connectivity(
        self,
        summaries: list[CameraSummary],
        *,
        agent_is_running: bool,
    ) -> list[CameraSummary]:
        """Checks camera connectivity via local agent. Cameras marked as unavailable if agent isn't running or unavailable"""
        if not summaries:
            return []

        if not agent_is_running:
            return[
                summary.with_status(
                    UNAVAILABLE,
                    "Local AI service is not running.",
                )
                for summary in summaries
            ]

        try:
            response = httpx.get(
                self.agent_status_url,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as error:
            logger.warning("Could not fetch camera status: %s", error)
            return[
                summary.with_status(
                    UNAVAILABLE,
                    "Could not reach local AI service.",
                )
                for summary in summaries
            ]

        status_by_id = {
            str(entry.get("id")): entry
            for entry in payload.get("cameras", [])
            if entry.get("id") is not None
        }

        updated: list[CameraSummary] = []

        for summary in summaries:
            entry = status_by_id.get(summary.id)

            if entry is None:
                #Camera configured but agent hasn't registered it yet
                updated.append(
                    summary.with_status(
                        CHECKING,
                        "Waiting for agent to pick up this camera.",
                    )
                )
                continue

            runtime_status = entry.get("status", CHECKING)

            if runtime_status == "connected":
                updated.append(summary.with_status(CONNECTED, None))
            elif runtime_status == "disconnected":
                updated.append(
                    summary.with_status(
                        DISCONNECTED,
                        "This camera could not be reached.",
                    )
                )
            else:
                updated.append(summary.with_status(CHECKING, None))

        return updated