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