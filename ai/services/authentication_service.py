from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import httpx

API_BASE_URL = "https://api.neighbourhoodwatchdog.co.za"

class CredentialStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid" #backend rejected key (401/403)
    UNAVAILABLE = "unavailable" #could not reach backend to check

@dataclass
class ValidationResult:
    status: CredentialStatus
    detail: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.status is CredentialStatus.VALID

class AuthenticationService:
    def __init__(self, 
                 base_url: str = API_BASE_URL, 
                 timeout_seconds: float = 5.0,
                 ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds