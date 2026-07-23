import tkinter as tk
from tkinter import ttk
import requests


class WatchDogPinPage(ttk.Frame):
    def connect_agent(self):
        # Get the PIN from the entry field
        self.pairing_pin = self.pin_entry.get().strip()

        # Validate PIN
        if not (self.pairing_pin.isdigit() and len(self.pairing_pin) == 9):
            self.log.config(state="normal")
            self.log.insert("end", "[ERROR] PIN must be exactly 9 digits.\n")
            self.log.see("end")
            self.log.config(state="disabled")
            return

        print(f"Entered PIN: {self.pairing_pin}")

        # Log message
        self.log.config(state="normal")
        self.log.insert("end", f"[INFO] Pairing PIN entered: {self.pairing_pin}\n")
        self.log.insert("end", "[INFO] Contacting server...\n")
        self.log.see("end")
        self.log.config(state="disabled")

        # API endpoint (NEEDS TO BE CHANGED IN THE FUTURE!!!)
        base_url = "http://localhost:8000"
        url = f"{base_url}/pairing-token/{self.pairing_pin}"

        try:
            response = requests.post(url, timeout=20)

            if response.ok:
                self.log.config(state="normal")
                self.log.insert("end", "[INFO] Pairing successful.\n")
                self.log.see("end")
                self.log.config(state="disabled")
            else:
                self.log.config(state="normal")
                self.log.insert(
                    "end",
                    f"[ERROR] Server returned {response.status_code}: {response.text}\n"
                )
                self.log.see("end")
                self.log.config(state="disabled")

        except requests.RequestException as e:
            self.log.config(state="normal")
            self.log.insert("end", f"[ERROR] Failed to connect: {e}\n")
            self.log.see("end")
            self.log.config(state="disabled")

    def validate_pin_input(self, value):
        # Allow deleting everything
        if value == "":
            return True

        # Only digits, maximum of 9 characters
        return value.isdigit() and len(value) <= 9
    
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

        vcmd = (self.register(self.validate_pin_input), "%P")

        self.pin_entry = ttk.Entry(
            pin_frame,
            width=18,
            font=("Consolas", 16),
            justify="center",
            validate="key",
            validatecommand=vcmd,
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