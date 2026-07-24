import json
import os
import sys
from pathlib import Pathv

def get_app_data_dir():
    """Returns a persisten, OS-appropriate directory for storing app data."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path))
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else: # Linux
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))

    app_dir = Path(base) / "WatchDog"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

CONFIG_PATH = get_app_data_dir() / "agent_config.json"

def save_config(data: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str) #default=str handles datetime datatype

def load_config() -> dict | None:
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)