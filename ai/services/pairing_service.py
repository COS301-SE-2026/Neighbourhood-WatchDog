import requests


API_BASE_URL = "https://api.neighbourhoodwatchdog.co.za"


class PairingError(Exception):
    """Raised when the agent cannot be paired successfully."""

def _sanitize_cameras(cameras: object) -> list[dict]:
    """
    Keep only camera data safe to persist in local configuration.
    """

    if not isinstance(cameras, list):
        return []

    safe_fields = {
        "id",
        "property_id",
        "neighbourhood_id",
        "name",
        "visibility",
        "location",
        "enabled",
        "created_at",
    }

    return [
        {
            field: camera[field]
            for field in safe_fields
            if field in camera
        }
        for camera in cameras
        if isinstance(camera, dict)
    ]

class PairingService:
    """Handles communication with the WatchDog backend for agent pairing."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def pair(self, pairing_token: str) -> dict:
        """
        Validate a pairing token with the backend.

        Returns:
            dict containing the API key and configuration returned
            by the backend.

        Raises:
            PairingError: if pairing fails.
        """

        url = (
            f"{self.base_url}/pairing-token/token/"
            f"{pairing_token}"
        )

        try:
            response = requests.get(url, timeout=20)

        except requests.RequestException as e:
            raise PairingError(
                "Unable to connect to the WatchDog server. "
                "Please check your internet connection and try again."
            ) from e

        if not response.ok:
            raise PairingError(
                f"Pairing failed. Server returned "
                f"status {response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as e:
            raise PairingError(
                "The WatchDog server returned an invalid response."
            ) from e

        inner = data.get("data", {})

        if not isinstance(inner, dict):
            raise PairingError(
                "The WatchDog server returned invalid pairing data."
            )

        api_key = inner.get("api_key")

        if not api_key:
            raise PairingError(
                "The pairing response did not contain an API key."
            )

        config = {
            key: value
            for key, value in inner.items()
            if key not in {"api_key", "cameras"}
        }

        config["cameras"] = _sanitize_cameras(
            inner.get("cameras")
        )

        return {
            "api_key": api_key,
            "config": config,
        }