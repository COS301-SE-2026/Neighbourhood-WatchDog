from __future__ import annotations

import queue
import threading

from tkinter import ttk, DoubleVar, StringVar

from services.benchmark_service import(
    BenchmarkResult,
    BenchmarkService,
    RATING_GOOD,
    RATING_MARGINAL,
    RATING_INSUFFICIENT,
    estimate_max_cameras,
)
from ui.theme import configure_log_text_widget