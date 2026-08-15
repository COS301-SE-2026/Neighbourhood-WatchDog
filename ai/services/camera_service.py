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

