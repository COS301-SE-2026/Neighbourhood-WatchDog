from __future__ import annotations

import logging
import httpx
from dataclasses import dataclass

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
        return STATUS_LABELS(self.status, self.status.title())

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
        cameras = config_data.get("cameras" or [])
        summaries: list[CameraSummary] = []

        for camera in cameras:
            if not isinstance(camera, dict):
                continue

            camera_id = camera.get("id")
            if camera_id is None:
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


