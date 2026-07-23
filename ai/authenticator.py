import tkinter as tk
from tkinter import ttk


class WatchDogPinPage(ttk.Frame):
    def connect_agent(self):
        # Get the PIN from the entry field
        self.pairing_pin = self.pin_entry.get().strip()

        print(f"Entered PIN: {self.pairing_pin}")

        #log message
        self.log.config(state="normal")
        self.log.insert("end", f"[INFO] Pairing PIN entered: {self.pairing_pin}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def __init__(self, parent):
        super().__init__(parent, padding=25)

        self.columnconfigure(0, weight=1)

        ttk.Label(
            self,
            text="WatchDog Agent Setup",
            font=("Segoe UI", 18, "bold")
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            self,
            text=(
                "To connect this computer to your WatchDog account, "
                "enter the 9-digit pairing PIN generated on the website. "
                "Once verified, the application will securely download "
                "your camera configuration and continue the setup."
            ),
            wraplength=700,
            justify="left"
        ).grid(row=1, column=0, sticky="w", pady=(10, 20))

        # Status

        self.status_label = ttk.Label(
            self,
            text="Status: Waiting for pairing PIN.",
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.grid(row=2, column=0, sticky="w", pady=(0, 15))

        # PIN Entry

        pin_frame = ttk.Frame(self)
        pin_frame.grid(row=3, column=0, sticky="w")

        ttk.Label(
            pin_frame,
            text="Pairing PIN:"
        ).pack(side="left", padx=(0, 10))

        self.pin_entry = ttk.Entry(
            pin_frame,
            width=18,
            font=("Consolas", 16),
            justify="center"
        )
        self.pin_entry.pack(side="left")

        ttk.Label(
            self,
            text="Example: 123456789",
            foreground="gray"
        ).grid(row=4, column=0, sticky="w", pady=(8, 20))

        # Progress
        ttk.Label(
            self,
            text="Connection Progress",
            font=("Segoe UI", 10, "bold")
        ).grid(row=5, column=0, sticky="w")

        self.progress = ttk.Progressbar(
            self,
            mode="determinate",
            length=700
        )
        self.progress.grid(row=6, column=0, sticky="ew", pady=(5, 15))

        # Log Output

        ttk.Label(
            self,
            text="Connection Log",
            font=("Segoe UI", 10, "bold")
        ).grid(row=7, column=0, sticky="w")

        log_frame = ttk.Frame(self)
        log_frame.grid(row=8, column=0, sticky="nsew")

        self.rowconfigure(8, weight=1)

        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")

        self.log = tk.Text(
            log_frame,
            height=16,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10)
        )
        self.log.pack(fill="both", expand=True)

        scrollbar.config(command=self.log.yview)

        # Example log lines
        self.log.insert("end", "[INFO] Waiting for pairing PIN...\n")
        self.log.insert("end", "[INFO] Agent is not yet connected.\n")
        self.log.config(state="disabled")

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=9, column=0, sticky="ew", pady=(20, 0))

        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.connect_button = ttk.Button(
            button_frame,
            text="Connect Agent",
            command=self.connect_agent
        )
        self.connect_button.grid(row=0, column=0, sticky="w")



        self.exit_button = ttk.Button(
            button_frame,
            text="Exit"
        )
        self.exit_button.grid(row=0, column=1, sticky="e")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("WatchDog Agent Setup")
    root.geometry("800x650")

    WatchDogPinPage(root).pack(fill="both", expand=True)

    root.mainloop()