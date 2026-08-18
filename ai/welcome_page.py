import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

SEGOUE_FONT = "Segoe UI"

class WelcomePage(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(
            parent,
            padding=24,
            style="App.TFrame",
        )

        self.controller = controller

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Title
        ttk.Label(
            self,
            text="Welcome to WatchDog",
            style="Title.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        # Description
        ttk.Label(
            self,
            text=(
                "WatchDog uses this computer to process camera footage "
                "locally and help protect your neighbourhood."
            ),
            style="Subtitle.TLabel",
            wraplength=700,
            justify="left",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(10, 20),
        )

        # Information card
        info_card = ttk.LabelFrame(
            self,
            text="Getting started",
            padding=16,
            style="Card.TLabelframe",
        )
        info_card.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        ttk.Label(
            info_card,
            text="Before you continue",
            style="Section.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        ttk.Label(
            info_card,
            text=(
                "• WatchDog will prepare a secure local AI environment on this computer.\n"
                "• You will then enter the pairing token generated from your WatchDog account.\n"
                "• After pairing, you can view your cameras and start local AI processing."
            ),
            style="CardBody.TLabel",
            justify="left",
            wraplength=650,
        ).pack(
            anchor="w",
        )

        # Bottom controls
        button_row = ttk.Frame(
            self,
            style="App.TFrame",
        )
        button_row.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(20, 0),
        )

        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)

        ttk.Button(
            button_row,
            text="Continue",
            command=self.on_next,
            style="Primary.TButton",
            width=16,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            button_row,
            text="Exit",
            command=self.on_cancel,
            style="Secondary.TButton",
            width=12,
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

    def on_next(self):
        self.controller.show_installer()

    def on_cancel(self):
        confirmed = messagebox.askyesno(
            "Exit WatchDog",
            "Exit WatchDog setup?"
        )

        if confirmed:
            self.winfo_toplevel().destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("WatchDog Agent Setup")
    root.geometry("800x650")

    class _DummyController:
        def show_installer(self):
            print("Next clicked -> would move to install page")

    WelcomePage(root, controller=_DummyController()).pack(fill="both", expand=True)
    root.mainloop()