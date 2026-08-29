from __future__ import annotations

import re
import shutil
import platform
import subprocess
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

AI_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = AI_DIR / ".watchdog-agent"
VENV_DIR = RUNTIME_DIR / "venv"
STATE_FILE = RUNTIME_DIR / "install-state.json"

WEIGHTS_DIR = AI_DIR / "pipeline" / "models" / "weights"
THREAT_MODEL_PATH = WEIGHTS_DIR / "best.pt"
PERSON_MODEL_PATH = WEIGHTS_DIR / "yolov8n.pt"

SUPPORTED_PYTHON = (3, 12)
INSTALL_SCHEMA_VERSION = 1

#Measured dependency disk size by installing dependencies on windows and linux
WINDOWS_SIZE = 2_020_000_000 #2.02GB
LINUX_SIZE = 8_010_000_000 #8.01GB

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

def get_dependency_bytes() -> int:
    """Returns measured dependency disk-space requirement for OS"""
    if platform.system() == "Linux":    
        return LINUX_SIZE

    return WINDOWS_SIZE

def get_available_disk_space(path: Path | None = None) -> int:
    """Returns avaliable disk space"""
    target = path | AI_DIR

    try:
        return shutil.disk_usage(target).free
    except OSError:
        return 0

def has_enough_disk_space(
        required_byetes: int | None = None,
        path: Path | None = None,
) -> bool:
    "Returns whether enough disk space to install dependencies"

    required = (required_byetes 
                if required_byetes is not None 
                else get_dependency_bytes()
    )

    available = get_available_disk_space(path)

    return available >= required

def get_disk_space_report() -> dict[str, int | bool]:
    """Returns disk space info needed by UI"""
    required = get_dependency_bytes()
    available = get_available_disk_space()

    return{
        "required_bytes": required,
        "available_bytes": available,
        "enough_space": available >= required,
    }

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

_REQUIREMENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._]+")

def _parse_requirement_names(path: Path, _seen: set[Path] | None = None) -> list[str]:
    """Extract top-level distribution names from requirements file"""
    seen = _seen if _seen is not None else set()

    if not path.is_file():
        return []

    resolved = path.resolve()
    if resolved in seen:
        return []
    seen.add(resolved)

    names: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        if line.startswith("-r "):
            included = (path.parent / line[3:].strip())
            names.extend(_parse_requirement_names(included, _seen=seen))
            continue

        match = _REQUIREMENT_NAME_PATTERN.match(line)
        if match:
            names.append(match.group(0))

    return names

def find_missing_packages(venv_python: Path, requirements_file: Path) -> list[str]:
    """returns list of missing packages that are not installed in the venv"""
    required_names = _parse_requirement_names(requirements_file)
    if not required_names:
        return []

    check_script = (
        "import importlib.metadata, sys\n"
        "missing = []\n"
        "for name in sys.argv[1:]:\n"
        "   try:\n"
        "       importlib.metadata.version(name)\n"
        "   except importlib.metadata.PackageNotFoundError:\n"
        "       missing.append(name)\n"
        "print(','.join(missing)\n)"
    )

    try:
        result = subprocess.run(
            [str(venv_python), "-c", check_script, *required_names],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return required_names

    if result.returncode != 0:
        return required_names

    missing = result.stdout.strip()
    return missing.split(",") if missing else []
@dataclass
class DependencyReport:
    """Holds list of problems found by dependency check"""
    problems: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.problems

class DependencyService:
    def __init__(
            self,
            *,
            venv_python: Path | None = None,
            state_file: Path | None = None,
            threat_model: Path | None = None,
            person_model: Path | None = None,
            requirements_file : Path | None = None,
            supported_python: tuple[int, int] = SUPPORTED_PYTHON,
            install_schema_version: int = INSTALL_SCHEMA_VERSION,
            ) -> None:
        self.venv_python = venv_python or get_venv_python()
        self.state_file = state_file or STATE_FILE
        self.threat_model = threat_model or THREAT_MODEL
        self.person_model = person_model or PERSON_MODEL
        self.requirements_file = requirements_file or REQUIREMENTS_FILE
        self.supported_python = supported_python
        self.install_schema_version = install_schema_version

    def check(self) -> DependencyReport:
        """Runs all dependency checks and returns list of problems found"""
        problems: list[str] = []

        if not self.venv_python.is_file():
            problems.append("venv_missing")
            return DependencyReport(problems=problems)

        missing_packages = find_missing_packages(self.venv_python, self.requirements_file)

        if missing_packages:
            problems.append(f"packages_missing:{','.join(missing_packages)}")
            return DependencyReport(problems=problems)
        
        if not model_is_valid(self.threat_model):
            problems.append("threat_model_invalid")
            
        if not model_is_valid(self.person_model):
            problems.append("person_model_invalid")

        if not self.state_file.is_file():
            problems.append("install_state_missing")
            return DependencyReport(problems=problems)

        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            problems.append("install_state_unreadable")
            return DependencyReport(problems=problems)

        if state.get("schema_version") != self.install_schema_version:
            problems.append("install_schema_outdated")

        installed_version = state.get("python_version", "")
        try:
            installed_major, installed_minor, *_ = (
                int(part) for part in installed_version.split(".")
            )
        except ValueError:
            problems.append("install_python_version_unknown")
        else:
            if (installed_major, installed_minor) < self.supported_python:
                problems.append("install_python_version_unsupported")

        return DependencyReport(problems=problems)

    def is_valid(self) -> bool:
        return self.check().is_valid

    def get_problems(self) -> list[str]:
        return self.check().problems