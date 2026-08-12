import sys
import tkinter as tk
from tkinter import ttk

from app_state import AppState
from main_app import MainApplicationPage
from startup import StartupDestination, StartupResolver
from watchdog_gui import WatchDogAgentApp
from authenticator import WatchDogPinPage


class WatchDogDesktopApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WatchDog Agent")
        self.root.geometry("800x650")

        self.configure_style()

        self.current_frame = None
        self.state = AppState()
        self.startup_resolver = StartupResolver()

        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

        self.start_application()

        self.root.mainloop()

    def configure_style(self) -> None:
        style = ttk.Style(self.root)

        if "vista" in style.theme_names() and sys.platform == "win32":
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

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

    def show_installer(self) -> None:
        self.show_page(WatchDogAgentApp)

    def show_pairing(self) -> None:
        self.show_page(WatchDogPinPage)

    def show_main_app(self) -> None:
        self.show_page(
            MainApplicationPage,
            state=self.state,
        )

    def quit_application(self) -> None:
        """
        Central shutdown point.

        Later this will stop AgentService and CameraSupervisor.
        """

        if self.current_frame is not None:
            on_close = getattr(self.current_frame, "on_close", None)

            if callable(on_close):
                on_close()

        self.root.destroy()


if __name__ == "__main__":
    WatchDogDesktopApp()