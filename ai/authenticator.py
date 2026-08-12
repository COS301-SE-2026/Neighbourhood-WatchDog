import tkinter as tk
from tkinter import ttk

from services.config_service import ConfigService
from services.keyring_service import KeyringService
from services.pairing_service import PairingService, PairingError


SEGOE_FONT = "Segoe UI"
KEY_RELEASE = "<KeyRelease>"


class WatchDogPinPage(ttk.Frame):

    def __init__(self, parent, controller=None):
        super().__init__(parent, padding=25)

        self.controller = controller

        # Services
        self.config_service = ConfigService()
        self.keyring_service = KeyringService()
        self.pairing_service = PairingService()

        self.columnconfigure(0, weight=1)

        # Title
        ttk.Label(
            self,
            text="WatchDog Agent Setup",
            font=(SEGOE_FONT, 18, "bold")
        ).grid(row=0, column=0, sticky="w")

        # Description
        ttk.Label(
            self,
            text=(
                "To connect this computer to your WatchDog account, "
                "enter the 9-character pairing token generated on the website. "
                "Once verified, the application will securely download "
                "your camera configuration and continue the setup."
            ),
            wraplength=700,
            justify="left"
        ).grid(row=1, column=0, sticky="w", pady=(10, 20))

        # Status
        self.status_label = ttk.Label(
            self,
            text="Status: Waiting for pairing token.",
            font=(SEGOE_FONT, 10, "bold")
        )
        self.status_label.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 15)
        )

        # Token Entry
        token_frame = ttk.Frame(self)
        token_frame.grid(row=3, column=0, sticky="w")

        ttk.Label(
            token_frame,
            text="Pairing Token:"
        ).pack(side="left", padx=(0, 10))

        # First block
        self.token_entry_1 = ttk.Entry(
            token_frame,
            width=4,
            font=("Consolas", 16),
            justify="center"
        )
        self.token_entry_1.pack(side="left")
        self.token_entry_1.bind(
            KEY_RELEASE,
            self.uppercase_entry
        )

        ttk.Label(
            token_frame,
            text="-"
        ).pack(side="left", padx=5)

        # Second block
        self.token_entry_2 = ttk.Entry(
            token_frame,
            width=4,
            font=("Consolas", 16),
            justify="center"
        )
        self.token_entry_2.pack(side="left")
        self.token_entry_2.bind(
            KEY_RELEASE,
            self.uppercase_entry
        )

        ttk.Label(
            token_frame,
            text="-"
        ).pack(side="left", padx=5)

        # Third block
        self.token_entry_3 = ttk.Entry(
            token_frame,
            width=4,
            font=("Consolas", 16),
            justify="center"
        )
        self.token_entry_3.pack(side="left")
        self.token_entry_3.bind(
            KEY_RELEASE,
            self.uppercase_entry
        )

        # Example
        ttk.Label(
            self,
            text="Example: ABC-123-XYZ",
            foreground="gray"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(8, 20)
        )

        # Progress
        ttk.Label(
            self,
            text="Connection Progress",
            font=(SEGOE_FONT, 10, "bold")
        ).grid(
            row=5,
            column=0,
            sticky="w"
        )

        self.progress = ttk.Progressbar(
            self,
            mode="determinate",
            length=700
        )
        self.progress.grid(
            row=6,
            column=0,
            sticky="ew",
            pady=(5, 15)
        )

        # Log Output
        ttk.Label(
            self,
            text="Connection Log",
            font=(SEGOE_FONT, 10, "bold")
        ).grid(
            row=7,
            column=0,
            sticky="w"
        )

        log_frame = ttk.Frame(self)
        log_frame.grid(
            row=8,
            column=0,
            sticky="nsew"
        )

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
        self.log.pack(
            fill="both",
            expand=True
        )

        scrollbar.config(
            command=self.log.yview
        )

        # Initial log messages
        self.log.insert(
            "end",
            "[INFO] Waiting for pairing token...\n"
        )
        self.log.insert(
            "end",
            "[INFO] Agent is not yet connected.\n"
        )
        self.log.config(
            state="disabled"
        )

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(
            row=9,
            column=0,
            sticky="ew",
            pady=(20, 0)
        )

        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.connect_button = ttk.Button(
            button_frame,
            text="Connect Agent",
            command=self.connect_agent
        )
        self.connect_button.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.back_button = ttk.Button(
            button_frame,
            text="Back",
            command=self.controller.show_installer
        )
        self.back_button.grid(
            row=0,
            column=1,
            sticky="e"
        )

    def exit_application(self):
        """Close the desktop application."""
        self.winfo_toplevel().destroy()

    def uppercase_entry(self, event):
        """Keep token input uppercase and limited to 3 characters."""
        widget = event.widget

        value = widget.get().upper()

        # Keep only letters and numbers
        value = "".join(
            character
            for character in value
            if character.isalnum()
        )

        # Maximum of 3 characters per block
        value = value[:3]

        widget.delete(0, tk.END)
        widget.insert(0, value)

    def connect_agent(self):
        """Validate the token and attempt to pair the desktop agent."""

        # Get token parts
        part1 = self.token_entry_1.get().strip().upper()
        part2 = self.token_entry_2.get().strip().upper()
        part3 = self.token_entry_3.get().strip().upper()

        # Token without dashes
        self.pairing_token = part1 + part2 + part3

        # Token in backend format
        self.formatted_pairing_token = (
            f"{part1}-{part2}-{part3}"
        )

        # ---------------------------------------------------------
        # Local validation
        # ---------------------------------------------------------

        if (
            len(part1) != 3
            or len(part2) != 3
            or len(part3) != 3
            or not self.pairing_token.isalnum()
        ):
            self.status_label.config(
                text="Status: Invalid pairing token."
            )

            self.log.config(state="normal")

            self.log.insert(
                "end",
                "[ERROR] Pairing token must contain exactly "
                "9 letters/numbers.\n"
            )

            self.log.see("end")
            self.log.config(state="disabled")

            return

        # ---------------------------------------------------------
        # Update UI while pairing
        # ---------------------------------------------------------

        self.status_label.config(
            text="Status: Contacting server..."
        )

        self.connect_button.config(
            state="disabled"
        )

        self.progress.config(
            mode="indeterminate"
        )
        self.progress.start(10)

        self.log.config(
            state="normal"
        )

        self.log.insert(
            "end",
            "[INFO] Pairing token entered.\n"
        )

        self.log.insert(
            "end",
            "[INFO] Contacting server...\n"
        )

        self.log.see("end")
        self.log.config(
            state="disabled"
        )

        self.update_idletasks()

        # ---------------------------------------------------------
        # Pair with backend
        # ---------------------------------------------------------

        try:
            result = self.pairing_service.pair(
                self.formatted_pairing_token
            )

            api_key = result["api_key"]
            config_data = result["config"]

            # Save configuration
            self.config_service.save(
                config_data
            )

            # Save API key securely in OS keyring
            self.keyring_service.save_api_key(
                api_key
            )

            # -----------------------------------------------------
            # Successful pairing
            # -----------------------------------------------------

            self.status_label.config(
                text="Status: Pairing successful."
            )

            self.log.config(
                state="normal"
            )

            self.log.insert(
                "end",
                "[INFO] Pairing successful.\n"
            )

            self.log.see("end")
            self.log.config(
                state="disabled"
            )

            # TODO:
            # This currently goes back to the installer because
            # that is how the old application flow works.
            #
            # This will eventually become:
            #
            # self.controller.show_main_app()
            #
            self.controller.show_main_app()

        except PairingError as e:

            # -----------------------------------------------------
            # Pairing failed
            # -----------------------------------------------------

            self.status_label.config(
                text="Status: Pairing failed."
            )

            self.log.config(
                state="normal"
            )

            self.log.insert(
                "end",
                f"[ERROR] {e}\n"
            )

            self.log.see("end")
            self.log.config(
                state="disabled"
            )

        finally:

            # Stop progress indicator
            if self.progress.winfo_exists():
                self.progress.stop()
                self.progress.config(
                    mode="determinate"
                )

            # Re-enable button
            if self.connect_button.winfo_exists():
                self.connect_button.config(
                    state="normal"
                )


if __name__ == "__main__":
    root = tk.Tk()
    root.title("WatchDog Agent Setup")
    root.geometry("800x650")

    WatchDogPinPage(
        root
    ).pack(
        fill="both",
        expand=True
    )

    root.mainloop()