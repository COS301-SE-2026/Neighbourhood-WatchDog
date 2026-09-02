from __future__ import annotations

from pathlib import Path

from app_config import get_app_data_dir

WELCOME_MARKER_FILE = get_app_data_dir() / "welcomed.marker"

class OnboardingService:
    "Tracks whether the welcome page has been shown"

    def __init__(self, marker_file: Path | None = None) -> None:
        self.marker_file = marker_file or WELCOME_MARKER_FILE

    def has_seen_welcome(self) -> bool:
        return self.marker_file.is_file()

    def mark_welcome_seen(self) -> None:
        self.marker_file.parent.mkdir(parents=True, exist_ok=True)
        self.marker_file.touch()