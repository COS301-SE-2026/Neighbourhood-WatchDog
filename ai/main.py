import queue
import logging
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from services.logging_service import configure_application_logging
from services.onboarding_service import OnboardingService
from app_state import AppState
from authenticator import WatchDogPinPage
from main_app import MainApplicationPage
from runtime.agent_runtime import AgentEvent
from services.agent_service import AgentService
from startup import StartupDestination, StartupResolver
from watchdog_gui import WatchDogAgentApp
from welcome_page import WelcomePage
from benchmark import BenchmarkPage
from ui.theme import configure_theme
from services.benchmark_service import BenchmarkResult
from services.benchmark_state_service import BenchmarkStateService
from services.config_service import ConfigService
from services.keyring_service import KeyringService

logger = logging.getLogger("watchdog.desktop.main")

class WatchDogDesktopApp:

    def __init__(self):
        configure_application_logging()
        logger.info("Starting WatchDog desktop application.")

        self.root = tk.Tk()
        self.root.title("WatchDog Agent")
        self.root.geometry("800x650")

        self.configure_style()

        self.current_frame = None
        self.state = AppState()
        self.startup_resolver = StartupResolver()
        self.onboarding_service = OnboardingService()
        self.benchmark_state_service = BenchmarkStateService()

        self.config_service = ConfigService()
        self.keyring_service = KeyringService()
        self.disconnect_in_progress = False

        self.agent_events: queue.Queue[AgentEvent] = queue.Queue()
        self.exit_requested = False

        self.agent_service = AgentService(
            event_callback=self.enqueue_agent_event,
        )

        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        self.root.after(100, self.process_agent_events)
        self.start_application()

        self.root.mainloop()

    def configure_style(self) -> None:
        configure_theme(self.root)

    def start_application(self) -> None:
        if not self.onboarding_service.has_seen_welcome():
            self.show_welcome()
            return
        
        decision = self.startup_resolver.resolve()
        self._apply_startup_decision(decision)

    def _apply_startup_decision(self, decision) -> None:
        """Shows the right page for each startup destination"""
        if decision.destination == StartupDestination.MAIN_APPLICATION:
            self.state = AppState.from_config(
                config_data=decision.config_data or {},
                api_key=decision.api_key,
            )
            self.show_main_app()
        elif decision.destination == StartupDestination.AUTHENTICATION:
            self.show_pairing()
        elif decision.destination == StartupDestination.INSTALLER:
            self.show_installer()
        elif decision.destination == StartupDestination.BENCHMARK:
            self.show_benchmark()
        else:
            logger.error(
                "Unhandled startup detination: %s (reason=%s)",
                decision.destination,
                decision.reason,
            )
            self.show_installer()
        
    def advance_past_welcome(self) -> None:
        """Called by welcome page's next button to skip setup/auth if already done"""
        self.onboarding_service.mark_welcome_seen()
        decision = self.startup_resolver.resolve()
        self._apply_startup_decision(decision)

    def advance_past_dependencies(self) -> None:
        """
        Show benchmark page (previously used to skip benchmark).
        """
        self.show_benchmark()
        # decision = self.startup_resolver.resolve_authentication()
        # self._apply_startup_decision(decision)

    def advance_past_benchmark(self) -> None:
        """Called after the required benchmark completes."""
        decision = self.startup_resolver.resolve_authentication()
        self._apply_startup_decision(decision)

    def show_page(self, page_class, **page_kwargs) -> None:
        if self.current_frame is not None:
            self.current_frame.destroy()

        self.current_frame = page_class(
            self.root,
            controller=self,
            **page_kwargs,
        )

        self.current_frame.pack(
            fill="both",
            expand=True,
        )

    def handle_pairing_success(
        self,
        api_key: str,
        config_data: dict,
    ) -> None:
        self.state = AppState.from_config(
            config_data=config_data,
            api_key=api_key,
        )
        self.show_main_app()

    def enqueue_agent_event(
        self,
        event: AgentEvent,
    ) -> None:
        """
        Called from AgentRuntime background threads.

        This method must not update Tkinter widgets directly.
        """

        self.agent_events.put(event)

    def process_agent_events(self) -> None:
        """
        Runs in the Tkinter main thread.

        It forwards runtime events to the current page safely.
        """

        try:
            while True:
                event = self.agent_events.get_nowait()

                if self.current_frame is not None:
                    handler = getattr(
                        self.current_frame,
                        "handle_agent_event",
                        None,
                    )

                    if callable(handler):
                        handler(event)

                if (
                    self.exit_requested
                    and event.event_type == "status"
                    and event.status == "stopped"
                ):
                    self.root.destroy()
                    return

        except queue.Empty:
            pass

        self.root.after(100, self.process_agent_events)

    def show_welcome(self) -> None:
        self.show_page(WelcomePage)

    def show_installer(self) -> None:
        self.show_page(WatchDogAgentApp)

    def show_benchmark(self) -> None:
        self.show_page(BenchmarkPage)

    def show_pairing(self) -> None:
        self.show_page(WatchDogPinPage)

    def show_main_app(self) -> None:
        self.show_page(
            MainApplicationPage,
            state=self.state,
            agent_service=self.agent_service,
        )

    def handle_benchmark_success(
        self,
        result: BenchmarkResult,
    ) -> None:
        """
        Save an accepted benchmark result.

        This method is called by BenchmarkPage.
        """
        self.benchmark_state_service.save(result)

    def request_disconnect(self) -> None:
        """
        Disconnect this desktop application from the current property.

        This is intentionally a local-only reset. It does not contact the
        backend or revoke the old backend credential.
        """

        if self.disconnect_in_progress:
            return

        confirmed = messagebox.askyesno(
            "Disconnect property",
            (
                "This will stop the local AI agent, remove the saved "
                "property connection from this computer, and require a "
                "new pairing token.\n\n"
                "The old backend credential will not be changed.\n\n"
                "Continue?"
            ),
        )

        if not confirmed:
            return

        self.disconnect_in_progress = True

        if self.agent_service.status in {
            "starting",
            "running",
            "running_with_warnings",
            "stopping",
        } or self.agent_service.is_running():
            self.agent_service.stop()

            self.root.after(
                100,
                self._wait_for_agent_stop_before_disconnect,
            )
            return

        self._begin_disconnect_worker()

    def _wait_for_agent_stop_before_disconnect(self) -> None:
        """
        Wait until the AI subprocess has stopped before clearing credentials.
        """

        if self.agent_service.is_running():
            self.root.after(
                100,
                self._wait_for_agent_stop_before_disconnect,
            )
            return

        if self.agent_service.status in {
            "starting",
            "stopping",
        }:
            self.root.after(
                100,
                self._wait_for_agent_stop_before_disconnect,
            )
            return

        self._begin_disconnect_worker()

    def _begin_disconnect_worker(self) -> None:
        """
        Clear local credentials away from the Tkinter UI thread.
        """

        threading.Thread(
            target=self._disconnect_worker,
            name="watchdog-local-disconnect",
            daemon=True,
        ).start()

    def _disconnect_worker(self) -> None:
        """
        Delete the local API key and persisted property configuration.

        No backend endpoint is called.
        """

        errors: list[str] = []

        try:
            self.keyring_service.clear_api_key()
        except Exception as error:
            logger.exception(
                "Could not clear the saved WatchDog API key."
            )
            errors.append(
                f"Could not clear the saved API key: {error}"
            )

        try:
            self.config_service.clear()
        except Exception as error:
            logger.exception(
                "Could not clear the saved WatchDog configuration."
            )
            errors.append(
                f"Could not clear the saved property configuration: {error}"
            )

        if errors:
            self.root.after(
                0,
                lambda: self._disconnect_failed(errors),
            )
            return

        self.root.after(
            0,
            self._restart_after_disconnect,
        )

    def _disconnect_failed(self, errors: list[str]) -> None:
        self.disconnect_in_progress = False

        messagebox.showerror(
            "Disconnect failed",
            (
                "WatchDog could not remove all local connection data.\n\n"
                + "\n".join(errors)
                + "\n\n"
                "The application will remain open so you can try again."
            ),
        )

    def _restart_after_disconnect(self) -> None:
        """
        Start a fresh WatchDog process, then close this process.
        """

        try:
            if getattr(sys, "frozen", False):
                command = [
                    sys.executable,
                    *sys.argv[1:],
                ]
                working_directory = (
                    Path(sys.executable).resolve().parent
                )
            else:
                script_path = Path(sys.argv[0]).resolve()
                command = [
                    sys.executable,
                    str(script_path),
                    *sys.argv[1:],
                ]
                working_directory = script_path.parent

            subprocess.Popen(
                command,
                cwd=str(working_directory),
                close_fds=True,
            )

        except OSError as error:
            logger.exception(
                "Could not restart WatchDog after disconnect."
            )

            messagebox.showerror(
                "Restart failed",
                (
                    "The local property connection was removed, but "
                    "WatchDog could not restart automatically.\n\n"
                    f"{error}"
                ),
            )

            self.root.destroy()
            return

        self.root.destroy()

    def quit_application(self) -> None:
        """
        Shut down the local AI service before closing the desktop app.
        """

        if self.exit_requested:
            return

        if self.agent_service.is_running():
            logger.info(
                "Desktop application exit requested while AI service is running."
            )

            self.exit_requested = True
            self.agent_service.shutdown()
            return

        logger.info("Closing WatchDog desktop application.")
        self.root.destroy()


if __name__ == "__main__":
    WatchDogDesktopApp()