import tkinter as tk
from tkinter import ttk
import sys

from watchdog_gui import WatchDogAgentApp, messagebox, SUPPORTED_PYTHON
from authenticator import WatchDogPinPage
from welcome_page import WelcomePage

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

        # Shared state — accessible from any page via self.controller
        self.api_key = None
        self.agent_id = None
        self.config_data = {}

        self.current_frame = None
        self.show_installer()
        self.root.mainloop()

    def show_page(self, page_class):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = page_class(self.root, controller=self)
        self.current_frame.pack(fill="both", expand=True)

    def show_welcome(self): #Wizard welcome page
        self.show_welcome(WelcomePage)

    def show_installer(self): #Install dependencies
        self.show_page(WatchDogAgentApp) 

    def show_pairing(self): #Links pairing token
        self.show_page(WatchDogPinPage)


if __name__ == "__main__":
    
    required = ".".join(map(str, SUPPORTED_PYTHON))
    current = f"{sys.version_info.major}.{sys.version_info.minor}"

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Unsupported Python Version",
        (
            f"WatchDog Agent requires Python {required}.x.\n\n"
            f"Current Python: {current}\n\n"
            "Install Python 3.12 and launch the application again."
        ),
    )
    root.destroy()
    raise SystemExit(1)

WatchDogDesktopApp()