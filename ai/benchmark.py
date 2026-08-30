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