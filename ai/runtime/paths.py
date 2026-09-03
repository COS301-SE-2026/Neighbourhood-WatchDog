from __future__ import annotations

import sys
from pathlib import Path


# Source/development directory.
# This is the ai/ directory when running normally from Python.
SOURCE_DIR = Path(__file__).resolve().parent.parent
AI_DIR = SOURCE_DIR

def is_packaged() -> bool:
    """
    Return True when running from a PyInstaller executable.
    """
    return bool(getattr(sys, "frozen", False))


def get_install_root() -> Path:
    """
    Return the root directory of the installed application.

    Expected packaged layout:

    WatchDog/
        WatchDog.exe
        service/
            WatchDogService.exe
        resources/
            pipeline/
            assets/
    """

    if not is_packaged():
        return SOURCE_DIR

    executable_directory = Path(sys.executable).resolve().parent

    # WatchDogService.exe will live inside WatchDog/service/.
    if executable_directory.name.lower() == "service":
        return executable_directory.parent

    # WatchDog.exe will live directly inside WatchDog/.
    return executable_directory


def get_resource_dir() -> Path:
    """
    Return the directory containing bundled read-only resources.
    """

    if not is_packaged():
        return SOURCE_DIR

    shared_resources = get_install_root() / "resources"

    if shared_resources.is_dir():
        return shared_resources

    # Fallback for a future one-file build or unusual PyInstaller layout.
    bundled_directory = getattr(sys, "_MEIPASS", None)

    if bundled_directory:
        return Path(bundled_directory)

    return get_install_root()


def get_service_executable() -> Path:
    """
    Return the packaged AI-service executable path.
    """

    return get_install_root() / "service" / "WatchDogService.exe"


# These are retained for development mode.
RUNTIME_DIR = SOURCE_DIR / ".watchdog-agent"
VENV_DIR = RUNTIME_DIR / "venv"


def get_venv_python() -> Path:
    """
    Return the development virtual-environment Python executable.
    """

    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"