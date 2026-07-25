import tkinter as tk
from tkinter import ttk

from installer_page import WatchDogAgentApp
from pairing_page import WatchDogPinPage


class WatchDogDesktopApp:
    def __init__(self):

        self.root = tk.Tk()
        self.root.title("WatchDog Agent")
        self.root.geometry("800x650")

        style = ttk.Style(self.root)

        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

        # Shared data
        self.api_key = None
        self.agent_id = None
        self.current_frame = None

        self.show_installer()

        self.root.mainloop()

    def show_page(self, page_class):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = page_class(
            self.root,
            controller=self,
        )

        self.current_frame.pack(fill="both", expand=True)

    def show_installer(self):
        self.show_page(WatchDogAgentApp)

    def show_pairing(self):
        self.show_page(WatchDogPinPage)


if __name__ == "__main__":
    WatchDogDesktopApp()