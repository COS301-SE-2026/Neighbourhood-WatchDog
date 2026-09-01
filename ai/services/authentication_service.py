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

    def validate_api_key(self, api_key: str | None) -> ValidationResult:
        """Checks api key with backend"""
        if not api_key:
            return ValidationResult(
                CredentialStatus.INVALID,
                "No API Key was provided.",
            )

        url = f"{self.base_url}/internal/cameras/summary"

        try:
            response = httpx.get(
                url,
                headers={"X-Internal-Token": api_key},
                timeout=self.timeout_seconds,
            )
        except httpx.RequestError as error:
            return ValidationResult(
                CredentialStatus.UNAVAILABLE,
                f"Could not reach the WatchDog server: {error}"
            )

        if response.status_code in (401, 403):
            return ValidationResult(
                CredentialStatus.INVALID,
                f"Server rejected the stored API key (status {response.status_code})."
            )

        if response.is_success:
            return ValidationResult(CredentialStatus.VALID)

        return ValidationResult(
            CredentialStatus.UNAVAILABLE,
            f"WatchDog server returned status {response.status_code}."
        )