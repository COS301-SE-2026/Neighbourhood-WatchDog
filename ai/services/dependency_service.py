from __future__ import annotations

import platform
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

AI_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = AI_DIR / ".watchdog-agent"
VENV_DIR = RUNTIME_DIR / "venv"
STALE_FILE = RUNTIME_DIR / "install-state.json"

WEIGHTS_DIR = AI_DIR / "pipeline" / "models" / "weights"
THREAT_MODEL_PATH = WEIGHTS_DIR / "best.pt"
PERSON_MODEL_PATH = WEIGHTS_DIR / "yolov8n.pt"

SUPPORTED_PYTHON = (3, 12)
INSTALL_SCHEMA_VERSION = 1

THREAT_MODEL = {
    "name": "Threat-detection model (best.pt)",
    "path": THREAT_MODEL_PATH,
    "url": "https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/download/weights-v1/best.pt",
    "expected_bytes": 6251747,
}

PERSON_MODEL = {
    "name": "Human-detection model (yolov8n.pt)",
    "path": PERSON_MODEL_PATH,
    "url": "https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/download/weights-v1/yolov8n.pt",
    "expected_bytes": 6549796,
}

def resolve_requirements_file() -> Path:
    """Determine what OS user is using, windows -> requirements.txt | WSL/Linux -> requirements-linux.txt"""
    if platform.system() == "Linux":
        candidate = AI_DIR / "requirements-linux.txt"
        if candidate.is_file():
            return candidate
    return AI_DIR / "requirements.txt"

REQUIREMENTS_FILE = resolve_requirements_file()

def get_venv_python() -> Path:
    """
    returning the file location of the python executable from the venv
    different os store the venv differently
    """
    #windows dir
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"

    #linux dir
    return VENV_DIR / "bin" / "python"

def format_bytes(value: int) -> str:
    """format bytes for readability in UI"""
    size = float(value)
    units = ["B", "KB", "MB", "GB"]

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{value} B"

def model_is_valid(model: dict) -> bool:
    """checks if model is valid via path dir and file size"""
    model_path: Path = model["path"]

    return (model_path.is_file() and model_path.stat().st_size == model["expected_bytes"])