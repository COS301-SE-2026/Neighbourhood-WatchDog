import tkinter as tk
from tkinter import ttk
import sys

from main_app import MainApplicationPage
from watchdog_gui import WatchDogAgentApp
from authenticator import WatchDogPinPage


class WatchDogDesktopApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WatchDog Agent")
        self.root.geometry("800x650")

        style = ttk.Style(self.root)
        if "vista" in style.theme_names() and sys.platform == "win32":
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

        # Shared application state
        self.api_key = None
        self.agent_id = None
        self.config_data = {}

        self.current_frame = None

        # Start application
        self.show_installer()

        self.root.mainloop()

    def show_page(self, page_class):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = page_class(
            self.root,
            controller=self
        )

        self.current_frame.pack(
            fill="both",
            expand=True
        )

    def show_installer(self):
        self.show_page(WatchDogAgentApp)

    def show_pairing(self):
        self.show_page(WatchDogPinPage)

    def show_main_app(self):
        self.show_page(MainApplicationPage)


if __name__ == "__main__":
    WatchDogDesktopApp()