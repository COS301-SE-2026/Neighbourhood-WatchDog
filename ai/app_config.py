import json
import os
import sys
from pathlib import Path


def get_app_data_dir():
    """Returns a persistent, OS-appropriate directory for storing app data."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home()))
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get(
            "XDG_CONFIG_HOME",
            str(Path.home() / ".config")
        )

    app_dir = Path(base) / "WatchDog"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


CONFIG_PATH = get_app_data_dir() / "agent_config.json"


def save_config(data: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_config() -> dict | None:
    if not CONFIG_PATH.exists():
        return None

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def clear_config() -> None:
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()