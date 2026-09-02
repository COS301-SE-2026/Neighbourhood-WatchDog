from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk, DoubleVar, StringVar

from services.benchmark_service import(
    BenchmarkResult,
    BenchmarkService,
    RATING_GOOD,
    RATING_LIMITED,
    RATING_INSUFFICIENT,
    estimate_max_cameras,
)
from ui.theme import configure_theme

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

        self.after(100, self.process_ui_events)
        self.show_benchmark_screen()

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

    def start_benchmark(self) -> None:
        """Starts the benchmark on background thread"""
        if self.benchmark_running:
            return

        if not self.benchmark_service.video_is_available():
            self.status_var.set("Required performance-check video is missing. Please reinstall WatchDog.")
            return
        
        self.benchmark_running = True

        if self.run_button is not None:
            self.run_button.configure(state="disabled")

        if self.skip_button is not None:
            self.skip_button.configure(state="disabled")

        self.progress_var.set(0)
        self._clear_results()
        self.status_var.set("Starting performance check...")

        worker = threading.Thread(
            target=self.run_benchmark_worker,
            name="watchdog-benchmark-worker",
            daemon=True,
        )
        worker.start()

    def run_benchmark_worker(self) -> None:
        """Runs on background thread, puts events on the queue"""
        def on_progress(message: str, fraction: float) -> None:
            self.emit("status", message)
            self.emit("progress", fraction * 100)

        result = self.benchmark_service.run(progress_callback=on_progress)
        self.emit("result", result)

    def emit(self, event_type: str, payload: object) -> None:
        """Queues event for TKinter mian thread to pick up"""
        self.events.put((event_type, payload))

    def _handle_status(self, payload) -> None:
        if self.status_var is not None:
            self.status_var.set(str(payload))

    def _handle_progress(self, payload) -> None:
        if self.progress_var is not None:
            self.progress_var.set(float(payload))

    def _handle_result(self, payload: BenchmarkResult) -> None:
        self.benchmark_running = False

        if self.run_button is not None:
            self.run_button.configure(state="normal")

        if self.skip_button is not None:
            self.skip_button.configure(state="normal")

        if not payload.is_valid:
            self.status_var.set("Performance check failed.")
            ttk.Label(
                self.results_frame,
                text=payload.error,
                style=MUTED_TLABEL,
                wraplength=650,
                justify="left",
            ).grid(row=0, column=0, columnspan=2, sticky="w")
            return

        self.status_var.set("Performance check complete.")
        self._render_results(payload)

        if payload.rating == RATING_INSUFFICIENT:# IF the rating is insufficient then we do not allow them to proceed
            self.status_var.set(
                "This computer may not be able to run WatchDog reliably."
            )

            if self.continue_button is not None:
                self.continue_button.configure(state="disabled")

            return

        if (
            self.controller is not None
            and hasattr(
                self.controller,
                "handle_benchmark_success",
            )
        ):
            self.controller.handle_benchmark_success(payload)
        
        if self.continue_button is not None:
            self.continue_button.configure(state="normal")

    def _clear_results(self) -> None:
        if self.results_frame is None:
            return

        for child in self.results_frame.winfo_children():
            child.destroy()

    def _render_results(self, result: BenchmarkResult) -> None:
        """Lays out measured metrics"""
        self._clear_results()

        max_cameras = estimate_max_cameras(result.avg_fps)

        rows = [
            ("Average FPS:", f"{result.avg_fps:.1f}"),
            ("Frame time (p95):", f"{result.p95_frame_time:.0f}"),
            ("Peak memory used:", f"{result.peak_memory:.0f} MB"),
            ("Peak CPU usage:", f"{result.peak_cpu_percent:.0f} %"),
            ("GPU:", result.gpu_name if result.gpu_available else "Not detected (running on CPU)"),
            ("Estimated camera capacity:", f"~{max_cameras} camera(s)"),
        ]

        for row_index, (label_text, value_text) in enumerate(rows):
            ttk.Label(
                self.results_frame,
                text=label_text,
                style=MUTED_TLABEL,
            ).grid(row=row_index, column=0, sticky="w", padx=(0, 20), pady=2)

            ttk.Label(
                self.results_frame,
                text=value_text,
            ).grid(row=row_index, column=1, sticky="w", pady=2)

        ttk.Label(
            self.results_frame,
            text=RATING_LABELS.get(result.rating, result.rating),
            font=(SEGOE_FONT, 10, "bold"),
            wraplength=650,
            justify="left",
        ).grid(
            row=len(rows),
            column=0,
            columnspan=2,
            sticky="w",
            pady=(12, 0),
        )

    def process_ui_events(self) -> None:
        """Polls queue on Tkinter main thread and uses handlers"""
        handlers = {
            "status": self._handle_status,
            "progress": self._handle_progress,
            "result": self._handle_result,
        }

        try:
            while True:
                event_type, payload = self.events.get_nowait()

                handler = handlers.get(event_type)
                if handler is not None:
                    handler(payload)
        except queue.Empty:
            pass

        self.after(100, self.process_ui_events)

    def go_next(self) -> None:
        """Hands off to controller to decide next step"""
        if self.controller is not None and hasattr(self.controller, "advance_past_benchmark"):
            self.controller.advance_past_benchmark()
            return

        print("Continue clicked -> would advance past the benchmark page")

    def skip_benchmark(self) -> None:
        "Lets user bypass the check entirely"
        self.go_next()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("WatchDog Agent Setup")
    root.geometry("800x650")

    configure_theme(root) #ONLY FOR DEVELOPMENT TESTING. REMOVE LATER. This should only be called once in main.py when the app starts.

    class _DummyController:
        def advance_past_benchmark(self):
            print("Continue/Skip clicked -> would move to pairing page")

    BenchmarkPage(root, controller=_DummyController()).pack(fill="both", expand=True)
    root.mainloop()