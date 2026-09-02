from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from runtime.agent_runtime import AgentEvent, AgentRuntime
from runtime.paths import (
    AI_DIR,
    get_service_executable,
    get_venv_python,
    is_packaged,
)


class AgentService:
    """
    Application-facing interface for the local WatchDog AI service.

    Tkinter pages should call this class instead of working with
    subprocesses, signals, ports, or Uvicorn commands directly.
    """

    def __init__(
        self,
        event_callback: Callable[[AgentEvent], None],
        *,
        ai_directory: Path | None = None,
        python_executable: Path | None = None,
        service_executable: Path | None = None,
    ) -> None:
        self.runtime = AgentRuntime(
            ai_directory=ai_directory or AI_DIR,
            python_executable=(
                python_executable or get_venv_python()
            ),
            service_executable=(
                service_executable
                or (
                    get_service_executable()
                    if is_packaged()
                    else None
                )
            ),
            event_callback=event_callback,
        )

    @property
    def status(self) -> str:
        return self.runtime.status

    def is_running(self) -> bool:
        return self.runtime.is_running()

    def start(self) -> bool:
        """
        Request startup of the local AI service.

        Returns False if the runtime is already running or cannot
        be started.
        """

        return self.runtime.start()

    def stop(self) -> bool:
        """
        Request a graceful stop of the local AI service.
        """

        return self.runtime.stop()

    def shutdown(self) -> None:
        """
        Request local AI-service shutdown during desktop-app exit.
        """

        self.runtime.shutdown()