import tkinter as tk
from tkinter import ttk

SEGOUE_FONT = "Segoe UI"

class WelcomePage(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, padding=25)
        self.controller = controller

        self.columnconfigure(0, weight=1)

        ttk.label(
            self,
            text="Welcome to WatchDog Agent",
            font=(SEGOUE_FONT, 20, "bold"),
            ).grid(row=0, column=0, sticky="w", pady=(0, 12))
        
        ttk.label(
            self,
            text=("This wizard sets up the WatchDog Agent on this computer by"
                  "installing the required dependencies and pairing it to your"
                  "WatchDog account.\n\n"
                  "Click Next to continue"
                  ),
            wraplength=680,
            justify="left"
            ).grid(row=1, column=0, sticky="w", pady=(0, 30))