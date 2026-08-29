from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from tkinter import Tk, messagebox, scrolledtext, StringVar, DoubleVar
from tkinter import ttk

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import traceback
import time
from ui.theme import configure_log_text_widget

from services.dependency_service import (
    AI_DIR,
    DependencyService,
    INSTALL_SCHEMA_VERSION,
    PERSON_MODEL,
    PERSON_MODEL_PATH,
    REQUIREMENTS_FILE,
    RUNTIME_DIR,
    STATE_FILE,
    SUPPORTED_PYTHON,
    THREAT_MODEL,
    THREAT_MODEL_PATH,
    VENV_DIR,
    WEIGHTS_DIR,
    format_bytes,
    get_venv_python,
    model_is_valid,
    get_available_disk_space,
    get_dependency_bytes,
    get_disk_space_report,
)

# CONSTANTS
SEGOE_FONT = "Segoe UI"
PARTITION_LINE = "============================"
ICON_CODE = "&#9679;"
APP_TFRAME = "App.TFrame"
MUTED_TLABEL = "Muted.TLabel"
REPAIR_INSTALLATION = "Repair Installation"
SECONDARY_TBUTTON = "Secondary.TButton"
SETUP_CANCELLED_BY_USER = "Setup cancelled by user."
class WatchDogAgentApp(ttk.Frame):

    def __init__(self, parent, controller=None) -> None:
        super().__init__(
            parent,
            padding=20,
            style=APP_TFRAME,
        )

        self.controller = controller
        self.root = parent
        self.dependency_service = DependencyService()

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.setup_running = False

        self.status_var = None
        self.progress_var = None
        self.disk_status_var = None
        self.progress_bar = None
        self.setup_button = None
        self.repair_button = None
        self.cancel_button = None
        self.log_box = None

        self.cancel_event = threading.Event()
        self.active_process: subprocess.Popen | None = None
        self._process_lock = threading.Lock()

        self.transitioning = False
        

        self.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_close)


        #polling messages from background
        self.after(100, self.process_ui_events)

        if self.dependency_service.is_valid():
            self.show_run_screen()
        else:
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
            style=APP_TFRAME,
        )
        outer.pack(fill="both", expand=True)

        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(8, weight=1)

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
            style=MUTED_TLABEL,
        ).grid(
            row=2,
            column=0,
            sticky="w",
        )

        if reason:
            ttk.Label(
                outer,
                text=reason,
                style=MUTED_TLABEL,
                wraplength=700,
                justify="left",
            ).grid(
                row=3,
                column=0,
                sticky="w",
                pady=(8, 0),
            )

        disk_report = get_disk_space_report()
        required_bytes = int(disk_report["required_bytes"])
        available_bytes = int(disk_report["available_bytes"])

        disk_frame = ttk.Frame(
            outer,
            padding=14,
            style=APP_TFRAME,
            relief="groove",
        )

        disk_frame.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(18,8),
        )

        disk_frame.columnconfigure(1, weight=1)

        ttk.Label(
            disk_frame,
            text="Disk Space",
            font=(SEGOE_FONT, 10, "bold"),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )

        ttk.Label(
            disk_frame,
            text="Required:",
            style=MUTED_TLABEL,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 20),
        )

        ttk.Label(
            disk_frame,
            text=format_bytes(required_bytes),
        ).grid(
            row=1,
            column=1,
            sticky="w",
        )

        ttk.Label(
            disk_frame,
            text="Available:",
            style=MUTED_TLABEL,
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 20),
        )

        ttk.Label(
            disk_frame,
            text=format_bytes(available_bytes),
        ).grid(
            row=2,
            column=1,
            sticky="w",
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
            style=APP_TFRAME,
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
            style=APP_TFRAME,
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
        button_frame.columnconfigure(3, weight=1)

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
            text=REPAIR_INSTALLATION,
            command=self.repair_installation,
            style=SECONDARY_TBUTTON,
            width=19,
        )

        self.repair_button.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(8, 8),
        )

        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_setup,
            style=SECONDARY_TBUTTON,
            width=12,
            state="disabled",
        )

        self.cancel_button.grid(
            row=0,
            column=2,
            sticky="e",
            padx=(8, 8),
        )

        ttk.Button(
            button_frame,
            text="Exit",
            command=self.on_close,
            style=SECONDARY_TBUTTON,
            width=12,
        ).grid(
            row=0,
            column=3,
            sticky="e",
        )


    def show_run_screen(self) -> None:
        self.clear_screen()

        outer = ttk.Frame(self, 
                padding=24,
                style=APP_TFRAME,)
        outer.pack(fill="both", expand=True)

        outer.columnconfigure(0, weight=1)

        ttk.Label(
             outer, 
             text="WatchDog Agent Setup", 
             style="Title.TLabel"
         ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            outer, 
            text="Setup complete: agent environment is ready.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(10, 4))

        ttk.Label(
            outer, 
            text=(
                "This computer is ready to connect to your WatchDog account"
                "Click Next to continue"
                ),
                style=MUTED_TLABEL,
                wraplength=700,
                justify="left" 
        ).grid(row=2, column=0, sticky="w", pady=(0, 16))

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
             style=MUTED_TLABEL,
             justify="left",
        ).grid(row=3, column=0, sticky="w", pady=(0, 12))

        button_frame = ttk.Frame(outer, style=APP_TFRAME)
        button_frame.grid(row=4, column=0, sticky="ew", pady=(20, 0))

        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.repair_button = ttk.Button(
            button_frame,
            text=REPAIR_INSTALLATION,
            command=self.repair_installation,
            style=SECONDARY_TBUTTON,
            width=19
        )
        self.repair_button.grid(row=0, column=0, sticky="w")

        self.next_button = ttk.Button(
            button_frame,
            text="Next >",
            command=self.go_next,
            style="Primary.TButton",
            width=12,
        )
        self.next_button.grid(row=0, column=1, sticky="e")
    
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

        self.cancel_event.clear()

        self.setup_running = True

        if self.setup_button is not None:
            self.setup_button.configure(state="disabled")

        if self.repair_button is not None:
            self.repair_button.configure(state="disabled")

        if self.cancel_button is not None:
            self.cancel_button.configure(state="normal")

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
            self._raise_if_cancelled()
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

            self._raise_if_cancelled()
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

            self._raise_if_cancelled()
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

            self._raise_if_cancelled()
            self.emit("status", "Applying Python 3.12 DeepSORT compatibility patch...")
            self.emit("progress", 45)

            self.patch_deep_sort(venv_python)

            self._raise_if_cancelled()
            self.download_model(
                model=THREAT_MODEL,
                progress_start=50, 
                progress_span=23
            )

            self._raise_if_cancelled()
            self.download_model(
                model=PERSON_MODEL,
                progress_start=73, 
                progress_span=22
            )

            self._raise_if_cancelled()
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

            if self.cancel_event.is_set():
                self.emit("cancelled", None)
                return
            
            self.emit("error", str(error))
            self.emit("log", "")
            self.emit("log", "=== Detailed setup error ===")
            self.emit("log", traceback.format_exc())
            self.emit("log", PARTITION_LINE)


    def _raise_if_cancelled(self) -> None:
        if self.cancel_event.is_set():
            raise RuntimeError(SETUP_CANCELLED_BY_USER)

    def _set_disk_status(self, report: dict[str, int | bool]) -> None:
        """Updates the setup screen with current disk space status"""
        if self.status_var is None:
            return

        shortage_bytes = int(report["shortage_bytes"])
        enough_space = bool(report["enough_space"])

        if enough_space:
            self.disk_status_var.set(
                "Enough disk space is available."
            )
        else:
            self.disk_status_var.set(
                f"Insufficient disk space. You need {format_bytes(shortage_bytes)} more before installation can begin."
            )
        
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

        with self._process_lock:
            self.active_process = process

        try: 
            assert process.stdout is not None

            for line in process.stdout:
                cleaned = line.rstrip()
                if cleaned:
                    self.emit("log", cleaned)

            return_code = process.wait()
        finally:
            with self._process_lock:
                if self.active_process is process:
                    self.active_process = None

        if self.cancel_event.is_set():
            raise RuntimeError(SETUP_CANCELLED_BY_USER)


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

        with self._process_lock:
            self.active_process = process

        try:
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
        finally:
            with self._process_lock:
                if self.active_process is process:
                    self.active_process = None

        if self.cancel_event.is_set():
            temporary_path.unlink(missing_ok=True)
            raise RuntimeError(SETUP_CANCELLED_BY_USER)
        
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
            "cancelled": self._handle_cancelled,
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

    def _handle_cancelled(self, _payload: object) -> None:
        self.setup_running = False
        self.stop_indeterminate_progress()

        if self.status_var is not None:
            self.status_var.set("Setup cancelld.")

        self.append_log("")
        self.append_log("Setup was cancelled.")

        if self.setup_button is not None:
            self.setup_button.configure(state="normal")

        if self.repair_button is not None:
            self.repair_button.configure(state="normal")

        if self.cancel_button is not None:
            self.cancel_button.configure(state="disabled")

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

    def go_next(self) -> None:
        """Hands off to controller to decide next step"""
        if self.controller is not None and hasattr(self.controller, "advance_past_dependencies"):
            self.controller.advance_past_dependencies()
            return

        print("Next clicked -> would advance past dependencies page")

    def repair_installation(self) -> None:
    
        #remove only the venv and installation marker.
        #model files are intentionally retained because they are large and may still be valid. Re-running setup validates them before reuse.
        if self.setup_running:
            return

        confirmed = messagebox.askyesno(
            REPAIR_INSTALLATION,
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
        
        if self.controller is not None:
            self.controller.quit_application()
        else:
            self.winfo_toplevel().destroy()

    def cancel_setup(self) -> None:
        """Cancels installation"""
        if not self.setup_running:
            return

        confirmed = messagebox.askyesno(
            "Cancel Setup",
            (
                "Stop the current installation?\n\n"
                "You can restart it later by clicking Set Up Agent again."
            ),
        )

        if not confirmed:
            return

        if self.cancel_button is not None:
            self.cancel_button.configure(state="disabled")

        self.append_log("")
        self.append_log("cancelling setup...")

        self.cancel_event.set()

        with self._process_lock:
            process = self.active_process

        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

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

    class _DummyController:
        def advance_past_dependencies(self):
            print("Next clicked -> would advance past dependencies")

        def quit_application(self):
            root.destroy()

    WatchDogAgentApp(root, controller=_DummyController()).pack(
        fill="both",
        expand=True,
    )
    root.mainloop()

#This should also be removed later so that this page cannot be run directly. It should only be run through the main.py file.
if __name__ == "__main__":
    main()
