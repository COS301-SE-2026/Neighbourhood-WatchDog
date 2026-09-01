import sys
from pathlib import Path


AI_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = AI_DIR / ".watchdog-agent"
VENV_DIR = RUNTIME_DIR / "venv"


def get_venv_python() -> Path:
    """
    Return the Python executable used by the local AI runtime.

    This is a development-mode helper. Packaging will replace this
    with a bundled runtime path later.
    """

    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"