from pathlib import Path
from runtime.agent_runtime import AgentRuntime, AgentEvent


class AgentService:

    def __init__(
        self,
        *,
        ai_directory: Path,
        python_executable: Path,
        event_callback,
    ) -> None:
        self.runtime = AgentRuntime(
            ai_directory=ai_directory,
            python_executable=python_executable,
            event_callback=event_callback,
        )

    def start(self) -> bool:
        return self.runtime.start()

    def stop(self) -> bool:
        return self.runtime.stop()

    def shutdown(self) -> None:
        self.runtime.shutdown()

    @property
    def status(self) -> str:
        return self.runtime.status