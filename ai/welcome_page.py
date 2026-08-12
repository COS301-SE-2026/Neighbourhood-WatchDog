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

        self.rowconfigure(2, weight=1)

        button_row = ttk.Frame(self)
        button_row.grid(row=3, column=0, sticky="ew")
        button_row.columnconfigure(0, weight=1)

        ttk.Button(
            button_row,
            text="Next >",
            command=self.on_next,
        ).pack(side="left")

        ttk.Button(
            button_row,
            text="Cancel"
        ).pack(side="left", padx=(10, 0))

        def on_next(self):
            self.controller.show_pairing()