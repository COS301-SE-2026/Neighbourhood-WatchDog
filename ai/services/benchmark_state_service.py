from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app_config import get_app_data_dir
from services.benchmark_service import BenchmarkResult

BENCHMARK_VERSION = 1

BENCHMARK_STATE_PATH = (
    get_app_data_dir() / "benchmark_state.json"
)


class BenchmarkStateService:
    """
    Persists the result of the local hardware benchmark.

    This file belongs in the user's application-data directory,
    not inside the packaged application folder.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or BENCHMARK_STATE_PATH

    def load(self) -> dict[str, Any] | None:
        """
        Load the saved benchmark state.

        Returns None when the file does not exist, is invalid,
        or does not contain a JSON object.
        """
        try:
            data = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return None

        if not isinstance(data, dict):
            return None

        return data

    def save(self, result: BenchmarkResult) -> None:
        """
        Save a completed benchmark result.
        """
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "completed": True,
            "rating": result.rating,
            "completed_at": (
                datetime.now(timezone.utc).isoformat()
            ),
            "benchmark_version": BENCHMARK_VERSION,
        }

        self.path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def has_accepted_result(self) -> bool:
        """
        Return True only for a completed Good or Limited result.
        """
        state = self.load()

        return bool(
            state
            and state.get("completed") is True
            and state.get("benchmark_version")
            == BENCHMARK_VERSION
            and state.get("rating") in {"good", "limited"}
        )

    def clear(self) -> None:
        """
        Remove the saved benchmark state.
        """
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass