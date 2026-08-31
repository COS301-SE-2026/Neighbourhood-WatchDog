from __future__ import annotations

import queue
import threading

from tkinter import ttk, DoubleVar, StringVar

from services.benchmark_service import(
    BenchmarkResult,
    BenchmarkService,
    RATING_GOOD,
    RATING_LIMITED,
    RATING_INSUFFICIENT,
    estimate_max_cameras,
)
from ui.theme import configure_log_text_widget

SEGOE_FONT = "Segoe UI"
APP_TFRAME = "App.TFrame"
MUTED_TLABEL = "Muted.TLabel"
SECONDARY_TBUTTON = "Secondary.TButton"

RATING_LABELS = {
    RATING_GOOD: "Good - this machine should run WatchDog comfortably.",
    RATING_LIMITED: "Limited - WatchDog will run, but consider connecting fewer cameras or lowering the resolution.",
    RATING_INSUFFICIENT: "Insufficient - this machine may struggle to keep up with real-time detection."
}

class BenchmarkPage(ttk.Frame):
    """
    Screen that runs BenchmarkService against test clip and reports whetehr the current
    machine can run WatchDog comfortably.
    """

    def __init__(self, parent, controller=None) -> None:
        super().__init__(parent, padding=20, style=APP_TFRAME)

        self.controller = controller
        self.root = parent
        self.benchmark_service = BenchmarkService()

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.benchmark_running = False

        self.status_var = None
        self.progress_var = None
        self.progress_bar = None
        self.run_button = None
        self.skip_button = None
        self.continue_button = None
        self.results_frame = None

    def clear_screen(self) -> None:
        for child in self.winfo_children():
            child.destroy() 

    def show_benchmark_screen(self) -> None:
        self.clear_screen()

        outer = ttk.Frame(self, padding=24, style=APP_TFRAME)
        outer.pack(fill="both", expand=True)

        outer.columnconfigure(0, weight=1)

        ttk.Label(
            outer,
            text="Performance Check",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            outer,
            text=(
                "WatchDog will run a short test using a sample video to "
                "check whether this computer can keep up with real-time "
                "person detection."
            ),
            style="Subtitle.TLabel",
            wraplength=700,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 16))

        self.status_var = StringVar(value="Ready to test this computer's performance.")

        ttk.Label(
            outer,
            textvariable=self.status_var,
            font=(SEGOE_FONT, 10, "bold"),
        ).grid(row=2, column=0, sticky="w", pady=(0, 8))

        self.progress_var = DoubleVar(value=0)

        self.progress_bar = ttk.Progressbar(
            outer,
            variable=self.progress_var,
            maximum=100,
            mode="determinate"
        )
        self.progress_bar.grid(row=3, column=0, sticky="ew", pady=(0, 16))

        self.results_frame = ttk.Frame(outer, style=APP_TFRAME)
        self.results_frame.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        self.results_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(outer, style=APP_TFRAME)
        button_frame.grid(row=5, column=0, sticky="ew", pady=(20, 0))

        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.run_button = ttk.Button(
            button_frame,
            text="Run Performance Check",
            command=self.start_benchmark,
            style="Primary.TButton",
            width=22,
        )
        self.run_button.grid(row=0, column=0, sticky="w")

        self.skip_button = ttk.Button(
            button_frame,
            text="Skip",
            command=self.skip_benchmark,
            style=SECONDARY_TBUTTON,
            width=12,
        )
        self.skip_button.grid(row=0, column=1)

        self.continue_button = ttk.Button(
            button_frame,
            text="Continue >",
            command=self.go_next,
            style="Primary.TButton",
            width=14,
            state="disabled",
        )
        self.continue_button.grid(row=0, column=2, sticky="e")