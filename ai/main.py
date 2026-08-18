import queue
import sys
import tkinter as tk
from tkinter import ttk
import logging

from services.logging_service import configure_application_logging
from app_state import AppState
from authenticator import WatchDogPinPage
from main_app import MainApplicationPage
from runtime.agent_runtime import AgentEvent
from services.agent_service import AgentService
from startup import StartupDestination, StartupResolver
from watchdog_gui import WatchDogAgentApp
from welcome_page import WelcomePage
from ui.theme import configure_theme

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
        decision = self.startup_resolver.resolve()

        if decision.destination == StartupDestination.MAIN_APPLICATION:
            self.state = AppState.from_config(
                config_data=decision.config_data or {},
                api_key=decision.api_key,
            )
            self.show_main_app()
            return

        self.show_installer()

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

    def show_pairing(self) -> None:
        self.show_page(WatchDogPinPage)

    def show_main_app(self) -> None:
        self.show_page(
            MainApplicationPage,
            state=self.state,
            agent_service=self.agent_service,
        )

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