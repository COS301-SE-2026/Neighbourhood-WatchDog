from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AgentEvent:
    event_type: str
    message: str
    status: str | None = None
    timestamp: datetime | None = None


class AgentRuntime:
    """
    Owns the local Uvicorn process that runs ai/app.py.

    This class must not depend on Tkinter.
    """

    def __init__(
        self,
        *,
        ai_directory: Path,
        python_executable: Path,
        event_callback: Callable[[AgentEvent], None],
        health_url: str = "http://127.0.0.1:8001/health",
    ) -> None:
        self.ai_directory = ai_directory
        self.python_executable = python_executable
        self.event_callback = event_callback
        self.health_url = health_url

        self._process: subprocess.Popen | None = None
        self._status = "stopped"
        self._stop_requested = False
        self._lock = threading.RLock()

        self._monitor_thread: threading.Thread | None = None
        self._log_thread: threading.Thread | None = None

    @property
    def status(self) -> str:
        with self._lock:
            return self._status


    def is_running(self) -> bool:
        with self._lock:
            return (
                self._process is not None
                and self._process.poll() is None
            )


    def _emit(
        self,
        event_type: str,
        message: str,
        status: str | None = None,
    ) -> None:
        self.event_callback(
            AgentEvent(
                event_type=event_type,
                message=message,
                status=status,
                timestamp=datetime.now(timezone.utc),
            )
        )


    def _set_status(
        self,
        status: str,
        message: str,
    ) -> None:
        with self._lock:
            self._status = status

        self._emit(
            event_type="status",
            message=message,
            status=status,
        )

   
    def start(self) -> bool:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._emit(
                    event_type="log",
                    message="The local AI service is already running.",
                )
                return False

        if not self.python_executable.is_file():
            self._set_status(
                "error",
                "Could not find the local AI runtime.",
            )
            self._emit(
                event_type="error",
                message=f"Missing Python executable: {self.python_executable}",
            )
            return False

        command = [
            str(self.python_executable),
            "-u",
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8001",
            "--no-access-log",
        ]

        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        environment["MKL_THREADING_LAYER"] = "GNU"

        popen_options = {
            "cwd": self.ai_directory,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "bufsize": 1,
            "env": environment,
        }

        if sys.platform == "win32":
            popen_options["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            popen_options["start_new_session"] = True

        self._set_status(
            "starting",
            "Starting local AI service...",
        )

        try:
            process = subprocess.Popen(command, **popen_options)
        except OSError as error:
            self._set_status(
                "error",
                "Could not start local AI service.",
            )
            self._emit(
                event_type="error",
                message=str(error),
            )
            return False

        with self._lock:
            self._process = process
            self._stop_requested = False

        self._emit(event_type="log", message="")
        self._emit(
            event_type="log",
            message="Starting WatchDog AI service...",
        )
        self._emit(
            event_type="log",
            message=f"$ {' '.join(command)}",
        )

        self._log_thread = threading.Thread(
            target=self._read_output,
            args=(process,),
            name="watchdog-agent-log-reader",
            daemon=True,
        )
        self._log_thread.start()

        self._monitor_thread = threading.Thread(
            target=self._monitor_process,
            args=(process,),
            name="watchdog-agent-monitor",
            daemon=True,
        )
        self._monitor_thread.start()

        return True

    def _read_output(self, process: subprocess.Popen) -> None:
        if process.stdout is None:
            return

        for line in process.stdout:
            message = line.rstrip()

            if message:
                self._emit(
                    event_type="log",
                    message=message,
                )


    def _monitor_process(
        self,
        process: subprocess.Popen,
    ) -> None:
        health_confirmed = False
        started_at = time.monotonic()
        health_timeout_seconds = 30

        while True:
            exit_code = process.poll()

            if exit_code is not None:
                with self._lock:
                    was_requested_stop = self._stop_requested

                    if self._process is process:
                        self._process = None

                if was_requested_stop:
                    self._set_status(
                        "stopped",
                        f"Stopped (exit code {exit_code}).",
                    )
                    self._emit(
                        event_type="log",
                        message="WatchDog AI service stopped.",
                    )
                else:
                    self._set_status(
                        "crashed",
                        f"AI service stopped unexpectedly (exit code {exit_code}).",
                    )
                    self._emit(
                        event_type="error",
                        message=(
                            "WatchDog AI service exited unexpectedly. "
                            "Review the agent log."
                        ),
                    )

                return

            if not health_confirmed:
                if self._check_health():
                    health_confirmed = True
                    self._set_status(
                        "running",
                        "Local AI service is running.",
                    )

                elif time.monotonic() - started_at > health_timeout_seconds:
                    self._set_status(
                        "error",
                        "The local AI service did not become ready.",
                    )
                    self._emit(
                        event_type="error",
                        message=(
                            "The health endpoint did not become available "
                            "within 30 seconds."
                        ),
                    )
                    self.stop()
                    health_confirmed = True

            # This continues even after status becomes "running".
            # That is how later crashes are detected.
            time.sleep(0.5)

    def _check_health(self) -> bool:
        try:
            with urllib.request.urlopen(
                self.health_url,
                timeout=1.0,
            ) as response:
                return response.status == 200

        except (urllib.error.URLError, OSError):
            return False

    def stop(self) -> bool:
        with self._lock:
            process = self._process

            if process is None or process.poll() is not None:
                self._process = None
                self._set_status("stopped", "Stopped.")
                return False

            if self._status == "stopping":
                return False

            self._stop_requested = True

        self._set_status(
            "stopping",
            "Stopping local AI service...",
        )
        self._emit(
            event_type="log",
            message="Stopping WatchDog AI service...",
        )

        threading.Thread(
            target=self._terminate_process_tree,
            args=(process,),
            name="watchdog-agent-stop-worker",
            daemon=True,
        ).start()

        return True


    def _terminate_process_tree(
        self,
        process: subprocess.Popen,
    ) -> None:
        try:
            if sys.platform == "win32":
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(process.pid, signal.SIGTERM)

            try:
                process.wait(timeout=10)

            except subprocess.TimeoutExpired:
                self._emit(
                    event_type="log",
                    message=(
                        "Stop timed out. Force-stopping remaining processes."
                    ),
                )

                if sys.platform == "win32":
                    subprocess.run(
                        [
                            "taskkill",
                            "/PID",
                            str(process.pid),
                            "/T",
                            "/F",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                else:
                    os.killpg(process.pid, signal.SIGKILL)

                process.wait(timeout=5)

        except (OSError, subprocess.SubprocessError) as error:
            self._set_status(
                "error",
                "Could not stop local AI service.",
            )
            self._emit(
                event_type="error",
                message=str(error),
            )

    def shutdown(self) -> None:
        self.stop()