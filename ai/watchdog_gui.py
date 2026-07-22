from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from tkinter import Tk, messagebox, scrolledtext
from tkinter import ttk


import json
import queue
import re
import shutil
import subprocess
import sys
import threading
import traceback
import urllib.error
import urllib.request



#APPLICATION PATHS

AI_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = AI_DIR / ".watchdog-agent"
VENV_DIR = RUNTIME_DIR / "venv"
STATE_FILE = RUNTIME_DIR / "install-state.json"
REQUIREMENTS_FILE = AI_DIR / "requirements.txt"

WEIGHTS_DIR = AI_DIR / "pipeline" / "models" / "weights"
THREAT_MODEL_PATH = WEIGHTS_DIR / "best.pt"
PERSON_MODEL_PATH = WEIGHTS_DIR / "yolov8n.pt"

SUPPORTED_PYTHON = (3, 12)
INSTALL_SCHEMA_VERSION = 1



THREAT_MODEL = {
    "name": "Threat-detection model (best.pt)", 
    "path": THREAT_MODEL_PATH,
    "url": ("https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/tag/weights-v1/best.pt"), 
    "expected_bytes": 6251747 

}

PERSON_MODEL = {
    "name": "Human-detection model (yolov8n.pt)", 
    "path": PERSON_MODEL_PATH, 
    "url": ("https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/tag/weights-v1/yolov8n.pt"), 
    "expected_bytes": 6549796 

}



def get_venv_python() -> Path:
    #returning the file location of the python executable from the venv
    #different os store the venv differently


    #windows dir
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"

    #linux dir
    return VENV_DIR / "bin" / "python"


def format_bytes(value: int) -> str:
    #format bytes for readability in UI

    size = float(value)
    units = ["B", "KB", "MB", "GB"]

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        
        size /= 1024

    return f"{value} B"


def model_is_valid(model: dict) -> bool:
    #checks if model is valid via path dir and file size

    model_path: Path = model["path"]

    return (model_path.is_file() and model_path.stat() == model["expected_bytes"])


def is_installation_valid() -> bool:

    vevn_python = get_venv_python()
    if not vevn_python:
        return False

    if not model_is_valid(THREAT_MODEL):
        return False

    if not model_is_valid(PERSON_MODEL):
        return False

    if not STATE_FILE.is_file():
        return False

    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False


    return (state.get("schema_version") == INSTALL_SCHEMA_VERSION and state.get("python_version", "").startswith("3.12"))



class WatchDogAgentApp:

    def __init__(self, root: Tk) -> None:

        self.root = root
        self.root.title("Neighbourhood WatchDog Agent")
        self.root.geometry("760x560")
        self.root.minsize(700, 500)

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.setup_running = False

        self.status_var = None
        self.progress_var = None
        self.progress_bar = None
        self.setup_button = None
        self.log_box = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


        #polling messages from background
        self.root.after(100, self.process_ui_events)

        if is_installation_valid():
            self.show_run_screen()
        else:
            self.show_setup_screen()


    #screen helper function
    def clear_screen(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()


    def show_setup_screen(self, reason: str="") -> None:

        self.clear_screen()

        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer, 
            text="WatchDog Agent Setup", 
            font=("Segoe UI", 20, "bold") 
        ).pack(anchor="w")


        ttk.Label(
            outer, 
            text=(
                "This one-time setup creates an isolated AI environment, "
                "installs dependencies, and downloads the detection models."
            ),
            wraplength=680,
            justify="left"
        ).pack(anchor="w", pady=(8, 12))


        python_text = (
            f"Detected Python: {sys.version.split()[0]} "
            f"({sys.executable})"
        )   

        ttk.Label(outer, text=python_text).pack(anchor="w")


        if reason:
            ttk.Label(
                outer, 
                text=reason,
                foreground="#b45309", 
                wraplength=680, 
                justify="left"
            ).pack(anchor="w", pady=(10, 0))


        self.status_var = ttk.StringVar(value="Ready to set up the WatchDog Agent.")
        ttk.Label(
            outer, 
            textvariable=self.status_var, 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(18, 6))


        self.progress_var = ttk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            outer, 
            variable=self.progress_var, 
            maximum=100, 
            mode="determinate"
        )


        self.progress_bar.pack(fill="x", pady=(0, 12))

        self.log_box = scrolledtext.ScrolledText(
            outer, 
            height=18, 
            wrap="word",
            state="disabled", 
            font=("Consolas", 9)
        )
        self.log_box.pack(fill="both", expand=True, pady=(0, 14))

        controls = ttk.Frame(outer)
        controls.pack(fill="x")


        self.setup_button = ttk.Button(
            controls, 
            text="Set Up Agent",
            command=self.start_setup
        )
        self.setup_button.pack(side="left")


        ttk.Button(
            controls, 
            text="Exit", 
            command=self.on_close 
        ).pack(side="right")


    def show_run_screen(self) -> None:

        self.clear_screen()

        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)


        ttk.Label(
            outer, 
            text="WatchDog Agent", 
            font=("Segou UI", 20, "bold")
        ).pack(anchor="w")


        ttk.Label(
            outer, 
            text="Setup complete: agent environment is ready.",
            foreground="#15803d",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(14, 8))


        ttk.Label(
            outer, 
            text=(
                "NEED TO ADD STOP/START CONTROLS HERE."
                "it'll launch the ai/app.py and the local ai service"
                ), 
                wraplength=680,
                justify="left" 
        ).pack(anchor="w", pady=(0, 24))



        details = (
            f"Python environment: {get_venv_python()}\n"
            f"Threat model: {THREAT_MODEL_PATH.name}"
            f"({format_bytes(THREAT_MODEL_PATH.stat().st_size)})\n"
            f"Person model: {PERSON_MODEL_PATH.name}"
            f"({format_bytes(PERSON_MODEL_PATH.stat().st_size)})\n"
        )


        ttk.Label(
            outer, 
            text=details, 
            justify="left"
        ).pack(anchor="w")


        controls = ttk.Frame(outer)
        controls.pack(fill="x", side="button", pady=(24, 0))


        ttk.Button(
            controls, 
            text="Repair Installation", 
            command=self.repair_installation
        ).pack(side="left")


        ttk.Button(
            controls, 
            text="Exit", 
            command=self.on_close
        ).pack(side="right")



    #setup lifecycle
    def start_setup(self) -> None:
        #start the installation without blocking the tkninter thread

        if self.setup_running:
            return

        if sys.version_info[:2] != SUPPORTED_PYTHON:
            required = ".".join(map(str, SUPPORTED_PYTHON))
            current = f"{sys.version_info.major}.{sys.version_info.minor}"

            messagebox.showerror(
                "Unsupported Python Version",
                (
                    f"WatchDog Agent currently requries Python {required}.x.\n\n"
                    f"This GUI was launched with Python {current}.\n\n"
                    "Install Python 3.12 and relaunch setup.bat."
                )
            )
            return


        if not REQUIREMENTS_FILE.is_file():
            messagebox.showerror(
                "Missing requirements.txt",
                f"Could not find:\n{REQUIREMENTS_FILE}"
            )
            return

        self.setup_running = True
        self.setup_button.configure(state="disabled")
        self.progress_var.set(0)

        self.append_log("Starting WatchDog Agent setup...")
        self.append_log(f"AI directory: {AI_DIR}")
        self.append_log("")

        worker = threading.Thread(
            target=self.run_setup_worker,
            name="watchdog-setup-worker",
            daemon=True
        )

        worker.start()


    def run_setup_worker(self) -> None:
        try:
            self.emit("status", "Preparing local folders...")
            self.emit("progress", 3)

            RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
            WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

            venv_python = get_venv_python()

            if not venv_python.is_file():
                self.emit("log", "Creating Python virtual environment...")
                self.emit("progess", 8)


                self.run_command_stream(
                    [sys.executable, "-m", "venv", str(VENV_DIR)],
                    "Virtual environment creation"
                )
            else:
                self.emit("log", "Existing virtual environment found - reusing it.")


            if not venv_python.is_file():
                raise RuntimeError(
                    "Virtual environment creation completed, but the venv "
                    "Python interpreter could not be found."
                )


            self.emit("status", "Upgrading pip...")
            self.emit("progress", 15)
            self.run_command_stream(
                [
                    str(venv_python), 
                    "-m", 
                    "pip", 
                    "install", 
                    "--upgrade",
                    "pip", 
                    "--disable-pip-version-check"
                ], 
                "Pip upgrade"
            )


            self.emit("status", "Installing AI depencies - this can take SEVERAL MINUTES...")
            self.emit("log", "")
            self.emit("log", "Installing requirements.")
            self.emit("indeterminate", True)


            try:
                self.run_command_stream(
                    [
                        str(venv_python),
                        "-m",
                        "pip", 
                        "install", 
                        "-r", 
                        str(REQUIREMENTS_FILE), 
                        "--timeout",
                        "300", 
                        "--disable-pip-version-check"
                    ],
                    "Dependency installation"
                )
            finally:
                self.emit("indeterminate", False)


            self.emit("status", "Applying Python 3.12 DeepSORT compatibility patch...")
            self.emit("progress", 45)

            self.patch_deep_sort(venv_python)

            self.download_model(
                model=THREAT_MODEL,
                progess_start=50, 
                progress_span=23
            )


            self.download_model(
                model=PERSON_MODEL,
                progress_start=73, 
                progress_span=22
            )

            self.emit("status", "Validating installations...")
            self.emit("progress", 97)


            if not model_is_valid(THREAT_MODEL):
                raise RuntimeError(f"Threat model validation failed: {THREAT_MODEL_PATH}")

            if not model_is_valid(PERSON_MODEL):
                raise RuntimeError(f"Person model validation failed: {PERSON_MODEL_PATH}")


            self.write_install_state()

            self.emit("progress", 100)
            self.emit("status", "Setup complete")
            self.emit("complete", None)
            



        except Exception as error:
            self.emit("indeterminate", False)
            self.emit("error", str(error))
            self.emit("log", "")
            self.emit("log", "=== Detailed setup error ===")
            self.emit("log", traceback.format_exc())
            self.emit("log", "============================")


    