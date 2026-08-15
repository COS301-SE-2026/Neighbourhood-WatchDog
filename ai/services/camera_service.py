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
    


