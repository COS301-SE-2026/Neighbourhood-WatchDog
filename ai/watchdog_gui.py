from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from tkinter import Tk, messagebox, scrolledtext, StringVar, DoubleVar
from tkinter import ttk
import platform


import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import traceback
import urllib.error
import urllib.request
import time
import signal
from ui.theme import configure_log_text_widget

def _resolve_requirements_file() -> Path:#Determine what OS user is using, windows -> requirements.txt | WSL/Linux -> requirements-linux.txt
    if platform.system() == "Linux":
        candidate = Path(__file__).parent / "requirements-linux.txt"
        if candidate.is_file():
            return candidate
    return Path(__file__).parent / "requirements.txt"

# CONSTANTS
SEGOE_FONT = "Segoe UI"
PARTITION_LINE = "============================"
ICON_CODE = "&#9679;"

#APPLICATION PATHS

AI_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = AI_DIR / ".watchdog-agent"
VENV_DIR = RUNTIME_DIR / "venv"
STATE_FILE = RUNTIME_DIR / "install-state.json"
REQUIREMENTS_FILE = _resolve_requirements_file()

WEIGHTS_DIR = AI_DIR / "pipeline" / "models" / "weights"
THREAT_MODEL_PATH = WEIGHTS_DIR / "best.pt"
PERSON_MODEL_PATH = WEIGHTS_DIR / "yolov8n.pt"

SUPPORTED_PYTHON = (3, 12)
INSTALL_SCHEMA_VERSION = 1



THREAT_MODEL = {
    "name": "Threat-detection model (best.pt)", 
    "path": THREAT_MODEL_PATH,
    "url": ("https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/download/weights-v1/best.pt"), 
    "expected_bytes": 6251747 

}

PERSON_MODEL = {
    "name": "Human-detection model (yolov8n.pt)", 
    "path": PERSON_MODEL_PATH, 
    "url": ("https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/releases/download/weights-v1/yolov8n.pt"), 
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

    return (model_path.is_file() and model_path.stat().st_size == model["expected_bytes"])


def is_installation_valid() -> bool:

    vevn_python = get_venv_python()
    if not vevn_python.is_file():
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

    installed_version = state.get("python_version", "")
    try:
        installed_major, installed_minor, *_ = (int(part) for part in installed_version.split("."))
    except ValueError:
        return False
    
    return (state.get("schema_version") == INSTALL_SCHEMA_VERSION and (installed_major, installed_minor) >= SUPPORTED_PYTHON)




class WatchDogAgentApp(ttk.Frame):

    def __init__(self, parent, controller) -> None:
        super().__init__(
            parent,
            padding=20,
            style="App.TFrame",
        )

        self.controller = controller
        self.root = parent
        # self.root.title("Neighbourhood WatchDog Agent")
        # self.root.geometry("760x560")
        # self.root.minsize(700, 500)

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.setup_running = False

        # self.agent_process = None
        # self.agent_status = "stopped"
        # self.agent_stop_requested = False
        # self.health_check_in_progress = False
        # self.exit_after_stop = False

        # self.agent_status_var = None
        # self.agent_status_label = None
        # self.agent_log_box = None
        # self.start_agent_button = None
        # self.stop_agent_button = None

        self.status_var = None
        self.progress_var = None
        self.progress_bar = None
        self.setup_button = None
        self.repair_button = None
        self.log_box = None

        self.transitioning = False
        

        self.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_close)


        #polling messages from background
        self.after(100, self.process_ui_events)

        # if is_installation_valid():
        #     self.show_run_screen()
        # else:
        #     self.show_setup_screen()
        self.show_setup_screen()


    #screen helper function
    def clear_screen(self) -> None:
        for child in self.winfo_children():
            child.destroy()


    def show_setup_screen(self, reason: str = "") -> None:
        self.clear_screen()

        outer = ttk.Frame(
            self,
            padding=24,
            style="App.TFrame",
        )
        outer.pack(fill="both", expand=True)

        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(7, weight=1)

        ttk.Label(
            outer,
            text="WatchDog Agent Setup",
            style="Title.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            outer,
            text=(
                "WatchDog needs to prepare this computer before it can "
                "run local AI camera processing."
            ),
            style="Subtitle.TLabel",
            wraplength=700,
            justify="left",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(10, 14),
        )

        python_text = (
            f"Detected Python: {sys.version.split()[0]} "
            f"({sys.executable})"
        )

        ttk.Label(
            outer,
            text=python_text,
            style="Muted.TLabel",
        ).grid(
            row=2,
            column=0,
            sticky="w",
        )

        if reason:
            ttk.Label(
                outer,
                text=reason,
                style="Muted.TLabel",
                wraplength=700,
                justify="left",
            ).grid(
                row=3,
                column=0,
                sticky="w",
                pady=(8, 0),
            )

        self.status_var = StringVar(
            value="Ready to prepare this computer."
        )

        ttk.Label(
            outer,
            textvariable=self.status_var,
            font=(SEGOE_FONT, 10, "bold"),
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(18, 8),
        )

        ttk.Label(
            outer,
            text="Installation Progress",
            font=(SEGOE_FONT, 10, "bold"),
        ).grid(
            row=5,
            column=0,
            sticky="w",
        )

        self.progress_var = DoubleVar(value=0)

        self.progress_bar = ttk.Progressbar(
            outer,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.grid(
            row=6,
            column=0,
            sticky="ew",
            pady=(5, 15),
        )

        ttk.Label(
            outer,
            text="Installation Log",
            font=(SEGOE_FONT, 10, "bold"),
        ).grid(
            row=7,
            column=0,
            sticky="w",
        )

        log_frame = ttk.Frame(
            outer,
            style="App.TFrame",
        )
        log_frame.grid(
            row=8,
            column=0,
            sticky="nsew",
            pady=(6, 0),
        )

        outer.rowconfigure(8, weight=1)

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            height=16,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        configure_log_text_widget(self.log_box)
        self.log_box.pack(
            fill="both",
            expand=True,
        )

        button_frame = ttk.Frame(
            outer,
            style="App.TFrame",
        )
        button_frame.grid(
            row=9,
            column=0,
            sticky="ew",
            pady=(20, 0),
        )

        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.setup_button = ttk.Button(
            button_frame,
            text="Set Up Agent",
            command=self.start_setup,
            style="Primary.TButton",
            width=18,
        )
        self.setup_button.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.repair_button = ttk.Button(
            button_frame,
            text="Repair Installation",
            command=self.repair_installation,
            style="Secondary.TButton",
            width=19,
        )

        self.repair_button.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(8, 8),
        )

        ttk.Button(
            button_frame,
            text="Exit",
            command=self.on_close,
            style="Secondary.TButton",
            width=12,
        ).grid(
            row=0,
            column=2,
            sticky="e",
        )


    # def show_run_screen(self) -> None:

    #     self.clear_screen()

    #     outer = ttk.Frame(self, padding=24)
    #     outer.pack(fill="both", expand=True)


    #     ttk.Label(
    #         outer, 
    #         text="WatchDog Agent", 
    #         font=("Segou UI", 20, "bold")
    #     ).pack(anchor="w")


    #     ttk.Label(
    #         outer, 
    #         text="Setup complete: agent environment is ready.",
    #         foreground="#15803d",
    #         font=(SEGOE_FONT, 11, "bold")
    #     ).pack(anchor="w", pady=(10, 4))


    #     ttk.Label(
    #         outer, 
    #         text=(
    #             "Start the local AI service to run detection and send"
    #             " annotaion data to the backend"
    #             ), 
    #             wraplength=680,
    #             justify="left" 
    #     ).pack(anchor="w", pady=(0, 16))


    #     #service status row
    #     status_row = ttk.Frame(outer)
    #     status_row.pack(fill="x", pady=(0, 12))


    #     self.agent_status_var = StringVar(value="&#9679;" "Stopped")
    #     self.agent_status_label = ttk.Label(
    #         status_row, 
    #         textvariable=self.agent_status_var, 
    #         foreground="#b91c1c", 
    #         font=(SEGOE_FONT, 11, "bold")

    #     )
    #     self.agent_status_label.pack(side="left")


    #     #start stop controls
    #     action_row = ttk.Frame(outer)
    #     action_row.pack(fill="x", pady=(0, 16))

    #     self.start_agent_button = ttk.Button(
    #         action_row, 
    #         text="Start Agent", 
    #         command=self.start_agent 

    #     )
    #     self.start_agent_button.pack(side="left")


    #     self.stop_agent_button = ttk.Button(
    #         action_row, 
    #         text="Stop Agent", 
    #         command=self.stop_agent, 
    #         state="disabled" 

    #     )
    #     self.stop_agent_button.pack(side="left", padx=(10, 0))



    #     self.pair_button = ttk.Button(
    #         action_row,
    #         text="Pair Agent",
    #         command=self.controller.show_pairing,
    #     )
    #     self.pair_button.pack(side="left", padx=5)


    #     #live service log
    #     ttk.Label(
    #         outer, 
    #         text="Agent Log", 
    #         font=(SEGOE_FONT, 10, "bold") 
    #     ).pack(anchor="w")

    #     self.agent_log_box = scrolledtext.ScrolledText(
    #         outer, 
    #         height=16, 
    #         wrap="word", 
    #         state="disabled", 
    #         font=("Consolas", 9) 
    #     )
    #     self.agent_log_box.pack(fill="both", expand=True, pady=(6, 12))



    #     details = (
    #         f"Python environment: {get_venv_python()}\n"
    #         f"Threat model: {THREAT_MODEL_PATH.name}"
    #         f"({format_bytes(THREAT_MODEL_PATH.stat().st_size)})\n"
    #         f"Person model: {PERSON_MODEL_PATH.name}"
    #         f"({format_bytes(PERSON_MODEL_PATH.stat().st_size)})\n"
    #     )


    #     ttk.Label(
    #         outer, 
    #         text=details, 
    #         justify="left"
    #     ).pack(anchor="w", pady=(0, 12))


    #     controls = ttk.Frame(outer)
    #     controls.pack(fill="x", side="bottom", pady=(8, 0))


    #     ttk.Button(
    #         controls, 
    #         text="Repair Installation", 
    #         command=self.repair_installation
    #     ).pack(side="left")


    #     ttk.Button(
    #         controls,
    #         text="Exit",
    #         command=self.on_close,
    #         style="Secondary.TButton",
    #     ).pack(side="right")

    #     self.set_agent_ui_state("stopped", "Stopped")



    #setup lifecycle
    def start_setup(self) -> None:
        #start the installation without blocking the tkninter thread

        if self.setup_running:
            return

        if sys.version_info[:2] < SUPPORTED_PYTHON:
            required = ".".join(map(str, SUPPORTED_PYTHON))
            current = f"{sys.version_info.major}.{sys.version_info.minor}"

            messagebox.showerror(
                "Unsupported Python Version",
                (
                    f"WatchDog Agent currently requries Python {required}.x.\n\n"
                    f"This GUI was launched with Python {current}.\n\n"
                    "Install Python 3.12 or newer and relaunch setup.bat."
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

        if self.setup_button is not None:
            self.setup_button.configure(state="disabled")

        if self.repair_button is not None:
            self.repair_button.configure(state="disabled")

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


            self.emit("status", "Installing AI dependencies - this can take SEVERAL MINUTES...")
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
                progress_start=50, 
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
            self.emit("log", PARTITION_LINE)



    def run_command_stream(self, command: list[str], description: str) -> None:
        #running a command and streams the output lines to the gui log

        self.emit("log", f"> {description}")
        self.emit("log", f"$ {' '.join(command)}")


        environment = os.environ.copy()
        environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"


        process = subprocess.Popen(
            command, 
            cwd=AI_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8", 
            errors="replace", 
            bufsize=1, 
            env=environment

        )


        assert process.stdout is not None


        for line in process.stdout:
            cleaned = line.rstrip()
            if cleaned:
                self.emit("log", cleaned)

        return_code = process.wait()


        if return_code != 0:
            raise RuntimeError(
                f"{description} failed with exit code {return_code}."
                "Check the setup log above for the package that failed."
            )


    def patch_deep_sort(self, venv_python: Path) -> None:

        marker = "WATCHDOG_PATCH_TARGET="

        locate_command = [
            str(venv_python),
            "-c", 
            (
                "import importlib.util; "
                "from pathlib import Path; "
                "spec = importlib.util.find_spec('deep_sort_realtime'); "
                "root = Path(next(iter(spec.submodule_search_locations))); "
                f"print('{marker}' + str(root / 'embedder' / 'embedder_pytorch.py'))"

            )
        ]


        result = subprocess.run(
            locate_command, 
            cwd = AI_DIR,
            text=True, 
            capture_output=True,
            encoding="utf-8", 
            errors="replace", 
            check=False
        )


        if result.returncode != 0:
            raise RuntimeError(
                "Could not locate deep_sort_realtime for the Python 3.12"
                f"compatibility patch:\n{result.stderr.strip()}"
            )

        target_line = next(
        (
            line
            for line in result.stdout.splitlines()
            if line.startswith(marker)
        ),
        None,
        )

        if target_line is None:
            raise RuntimeError(
                "Could not determine the DeepSORT patch target. "
                f"Command output was:\n{result.stdout.strip()}"
            )


        patch_path_text = target_line.split(marker, 1)[1].strip()
        patch_file = Path(patch_path_text)

        if not patch_file.is_file():
            raise RuntimeError(
                f"DeepSORT patch target was not found:\n{patch_file}"

            )

        content = patch_file.read_text(encoding="utf-8")


        if "pkg_resources" not in content:
            self.emit("log", "DeepSORT compatibility patch is already applied or not required.")
            return


        patched = content
        patched = patched.replace("import pkg_resources", "import os as _os")
        patched = patched.replace("from setuptools import pkg_resources", "import os as _os")



        patched = re.sub(
            r"pkg_resources\.resource_filename\(\s*['\"]deep_sort_realtime['\"]\s*,\s*",
            "_os.path.join(_os.path.dirname(_os.path.dirname(__file__)), ",
            patched 
        )



        if patched == content or "pkg_resources" in patched:
            raise RuntimeError(
                "The DeepSORT compatibility patch could not safely transform "
                "embedder_pytorch.py. Review the installed package source."
            )


        patch_file.write_text(patched, encoding="utf-8")
        self.emit("log", "Applied DeepSORT Python 3.12 compatibility patch.")



    def download_model(self, model: dict, progress_start: float, progress_span: float,) -> None:

        model_path: Path = model["path"]
        expected_bytes: int = model["expected_bytes"]

        if model_is_valid(model):
            self.emit(
                "log",
                f"{model['name']} already exists and passed size validation — skipping.",
            )
            self.emit("progress", progress_start + progress_span)
            return

        curl_path = shutil.which("curl")

        if curl_path is None:
            raise RuntimeError(
                "curl was not found. Install curl, then retry setup. "
                "It is normally included with Windows 10/11 and Linux distributions."
            )

        model_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = model_path.with_suffix(model_path.suffix + ".part")
        temporary_path.unlink(missing_ok=True)

        self.emit(
            "status",
            f"Downloading {model['name']}...",
        )
        self.emit(
            "log",
            f"Downloading {model['name']} ({format_bytes(expected_bytes)})...",
        )

        command = [
            curl_path,
            "--http1.1",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--retry",
            "3",
            "--retry-delay",
            "3",
            "--connect-timeout",
            "30",
            "--output",
            str(temporary_path),
            model["url"],
        ]

        process = subprocess.Popen(
            command,
            cwd=AI_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Poll the growing .part file to provide byte-level progress to Tkinter.
        while process.poll() is None:
            if temporary_path.exists():
                downloaded = temporary_path.stat().st_size
                ratio = min(downloaded / expected_bytes, 1.0)

                self.emit(
                    "progress",
                    progress_start + (progress_span * ratio),
                )
                self.emit(
                    "status",
                    (
                        f"Downloading {model_path.name}: "
                        f"{format_bytes(downloaded)} / "
                        f"{format_bytes(expected_bytes)}"
                    ),
                )

            time.sleep(0.2)

        _, stderr_output = process.communicate()

        if process.returncode != 0:
            temporary_path.unlink(missing_ok=True)

            raise RuntimeError(
                f"Failed to download {model['name']} with curl.\n"
                f"curl error:\n{stderr_output.strip()}"
            )

        if not temporary_path.exists():
            raise RuntimeError(
                f"{model['name']} download finished but no temporary file was created."
            )

        actual_size = temporary_path.stat().st_size

        if actual_size != expected_bytes:
            temporary_path.unlink(missing_ok=True)

            raise RuntimeError(
                f"{model['name']} download is incomplete or invalid. "
                f"Expected {expected_bytes} bytes but received {actual_size} bytes."
            )

        temporary_path.replace(model_path)

        self.emit(
            "progress",
            progress_start + progress_span,
        )
        self.emit(
            "log",
            f"Downloaded and validated {model['name']}.",
        )
    
    def write_install_state(self) -> None:

        state = {
            "schema_version": INSTALL_SCHEMA_VERSION, 
            "python_version": sys.version.split()[0], 
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "models": {
                THREAT_MODEL_PATH.name: THREAT_MODEL_PATH.stat().st_size, 
                PERSON_MODEL_PATH.name: PERSON_MODEL_PATH.stat().st_size
            }
        }


        temporary_state = STATE_FILE.with_suffix(".json.part")


        temporary_state.write_text(
            json.dumps(state, indent=2), 
            encoding="utf-8"
        )


        temporary_state.replace(STATE_FILE)
        self.emit("log", f"Installation state saved to: {STATE_FILE}")


    def emit(self, event_type: str, payload: object) -> None:
        self.events.put((event_type, payload))


    def process_ui_events(self) -> None:

        handlers ={
            "log": self._handle_log,
            "status": self._handle_status,
            "progress": self._handle_progress,
            "indeterminate": self._handle_indeterminate,
            "complete": self._handle_complete,
            "error": self._handle_error,
            # "agent_log": self._handle_agent_log,
            # "agent_health": self._handle_agent_health,
            # "agent_stop_error": self._handle_agent_stop_error
        }

        try:
            while True:
                event_type, payload = self.events.get_nowait()

                handler = handlers.get(event_type)
                if handler is not None:
                    handler(payload)

        except queue.Empty:
            pass


        if not self.transitioning:
            self.after(100, self.process_ui_events)


    def _handle_log(self, payload) -> None:
        self.append_log(str(payload))


    def _handle_status(self, payload) -> None:
        if self.status_var is not None:
            self.status_var.set(str(payload))


    def _handle_progress(self, payload) -> None:
        self.stop_indeterminate_progress()

        if self.progress_var is not None:
            self.progress_var.set(float(payload))


    def _handle_indeterminate(self, payload) -> None:
        if bool(payload):
            self.start_indeterminate_progress()
        else:
            self.stop_indeterminate_progress()


    def _handle_complete(self, _payload: object) -> None:
        self.setup_running = False
        self.stop_indeterminate_progress()
        self.transitioning = True

        self.winfo_toplevel().after_idle(
            self.controller.show_pairing
        )


    def _handle_error(self, payload) -> None:
        self.setup_running = False
        self.stop_indeterminate_progress()

        if self.status_var is not None:
            self.status_var.set("Setup failed. Review the log and retry.")

        self.append_log("")
        self.append_log(f"ERROR: {payload}")

        if self.setup_button is not None:
            self.setup_button.configure(state="normal")

        if self.repair_button is not None:
            self.repair_button.configure(state="normal")

        messagebox.showerror(
            "WatchDog Agent Setup Failed",
            (
                "The agent was not fully installed.\n\n"
                "Review the setup log for details, correct the issue, "
                "and click Set Up Agent to retry."
            )
        )


    # def _handle_agent_log(self, payload) -> None:
    #     self.append_agent_log(str(payload))


    # def _handle_agent_health(self, payload) -> None:
    #     self.health_check_in_progress = False

    #     is_running = (bool(payload) and self.agent_process is not None and self.agent_process.poll() is None)

    #     if is_running and self.agent_status != "running":
    #         self.set_agent_ui_state("running", "Running: local AI service is healthy")


    # def _handle_agent_stop_error(self, payload) -> None:
    #     self.exit_after_stop = False
    #     self.set_agent_ui_state("error", "Could not stop service")

    #     self.append_agent_log(f"ERROR: {payload}")

    #     messagebox.showerror("Agent Stop Failed", str(payload))

    def start_indeterminate_progress(self) -> None:
        if self.progress_bar is None:
            return

        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start(12)


    def stop_indeterminate_progress(self) -> None:
        if self.progress_bar is None:
            return

        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")


    def append_log(self, message: str) -> None:
        #add text to setup log if the screen is active
        if self.log_box is None:
            return

        try:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"{message}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        except Exception:
            #the screen may have changed while queued events were draining.
            pass


    # def set_agent_ui_state(self, state: str, message: str) -> None:
    #     #update run screen status and its button availabilitty
    #     self.agent_status = state

    #     colours = {
    #         "stopped": "#b91c1c", 
    #         "starting": "#b45309", 
    #         "running": "#15803d", 
    #         "stopping": "#b45309", 
    #         "error": "#b91c1c"
    #     }

    #     status_icons = {
    #         "stopped": ICON_CODE, 
    #         "starting": ICON_CODE, 
    #         "running": ICON_CODE, 
    #         "stopping": ICON_CODE, 
    #         "error": ICON_CODE
    #     }

    #     if self.agent_status_var is not None:
    #         self.agent_status_var.set(f"{status_icons[state]} {message}")

    #     if self.agent_status_label is not None:
    #         self.agent_status_label.configure(foreground=colours.get(state, "#111827"))

    #     if self.start_agent_button is not None:
    #         self.start_agent_button.configure(
    #             state=(
    #                 "normal"
    #                 if state in {"stopped", "error"}
    #                 else "disabled"
    #             )
    #         )


    #     if self.stop_agent_button is not None:
    #         self.stop_agent_button.configure(
    #             state=(
    #                 "normal"
    #                 if state in {"starting", "running"}
    #                 else "disabled"
    #             )
    #         )


    # def append_agent_log(self, message: str) -> None:
    #     #appends the ai service line to the run screen live log

    #     if self.agent_log_box is None:
    #         return

    #     try:
    #         self.agent_log_box.configure(state="normal")
    #         self.agent_log_box.insert("end", f"{message}\n")
    #         self.agent_log_box.see("end")
    #         self.agent_log_box.configure(state="disabled")
    #     except Exception:
    #         pass

    # def start_agent(self) -> None:
    #     if self.controller is None or self.controller.agent_service is None:
    #         self.set_agent_ui_state(
    #             "error",
    #             "Agent controls are not available",
    #         )
    #         return

    #     self.controller.agent_service.start()

    # def stop_agent(self) -> None:
    #     if self.controller is None or self.controller.agent_service is None:    
    #         return
        
    #     self.controller.agent_service.stop()

    # def handle_agent_event(self, event) -> None:
    #     if event.event_type == "status":
    #         self.set_agent_ui_state(
    #             event.status or "error",
    #             event.message,
    #         )

    #     elif event.event_type == "error":
    #         self.set_agent_ui_state("error", event.message)

    #     elif event.event_type == "log":
    #         self.append_agent_log(event.message)

    def repair_installation(self) -> None:
    
        #remove only the venv and installation marker.
        #model files are intentionally retained because they are large and may still be valid. Re-running setup validates them before reuse.
        if self.setup_running:
            return

        confirmed = messagebox.askyesno(
            "Repair Installation",
            (
                "This removes the local Python environment and setup marker, "
                "then returns to Setup.\n\n"
                "Validated model files will be retained.\n\n"
                "Continue?"
            ),
        )

        if not confirmed:
            return

        try:
            if VENV_DIR.exists():
                shutil.rmtree(VENV_DIR)

            STATE_FILE.unlink(missing_ok=True)

        except OSError as error:
            messagebox.showerror(
                "Repair Failed",
                f"Could not reset the installation:\n{error}",
            )
            return

        self.show_setup_screen(
            "Installation reset. Click Set Up Agent to recreate the environment."
        )

    def on_close(self) -> None:
        #avoid closing the app during an active installation.
        if self.setup_running:
            messagebox.showwarning(
                "Setup Is Running",
                (
                    "The WatchDog Agent is still installing dependencies or "
                    "downloading models. Please wait for it to finish or fail "
                    "before closing the application."
                ),
            )
            return

        self.controller.quit_application()
# Main needs to be removed later so that this page cannot be run directly. It should only be run through the main.py file.
def main() -> None:
    if sys.version_info[:2] < SUPPORTED_PYTHON:
        required = ".".join(map(str, SUPPORTED_PYTHON))
        current = f"{sys.version_info.major}.{sys.version_info.minor}"

        root = Tk()
        root.withdraw()

        messagebox.showerror(
            "Unsupported Python Version",
            (
                f"WatchDog Agent requires Python {required}.x.\n\n"
                f"Current Python: {current}\n\n"
                "Install Python 3.12 or newer and launch the application again."
            ),
        )

        root.destroy()
        raise SystemExit(1)

    root = Tk()

  
    style = ttk.Style(root)
    available_themes = style.theme_names()

    if "vista" in available_themes and sys.platform == "win32":
        style.theme_use("vista")
    elif "clam" in available_themes:
        style.theme_use("clam")

    WatchDogAgentApp(root)
    root.mainloop()

#This should also be removed later so that this page cannot be run directly. It should only be run through the main.py file.
if __name__ == "__main__":
    main()
