from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from services.dependency_service import (
    PERSON_MODEL_PATH,
    get_venv_python,
)
from runtime.paths import get_resource_dir, get_service_executable, is_packaged

BENCHMARK_VIDEO_PATH = (
    get_resource_dir()
    / "assets"
    / "clear-presence.mp4"
)
RUNNER_SCRIPT_PATH = Path(__file__).resolve().parent / "benchmark_runner.py"

#30 frames run through the detector first without tiuming 
#to allow loading the model and starting up the GPU
WARMUP_FRAMES = 30

#How long the timed portion of the benchmark runs for. 
#Clip loops if shorter than 45s
BENCHMARK_DURATION = 45.0

#Modest thresholds to determine if hardware can process AI detection
MIN_FPS_PER_CAMERA_GOOD = 10.0 #10+ FPS -> runs comfortably
MIN_FPS_PER_CAMERA_LIMITED = 6.0 #6-10 -> usable, but tight

RATING_GOOD = "good"
RATING_LIMITED = "limited"
RATING_INSUFFICIENT = "insufficient"

ProgressCallback = Callable[[str, float], None]

@dataclass
class BenchmarkResult:
    """Contains the measured performance data from a single benchmark run"""
    frames_processed: int = 0
    duration: float = 0.0
    avg_fps: float = 0.0
    p95_frame_time: float = 0.0 #milliseconds
    peak_memory: float = 0.0
    peak_cpu_percent: float = 0.0
    gpu_available: bool = False
    gpu_name: str | None = None
    peak_gpu_memory: float = 0.0
    rating: str = RATING_INSUFFICIENT
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.error is None

class BenchmarkService:
    """
    Runs the detection pipeline against a test clip to benchmark the user's hardware
    To determine whether they can comfortably run the local AI processing
    """
    def __init__(
            self,
            *,
            video_path: Path | None = None,
            person_model_path: Path | None = None,
            venv_python: Path | None = None,
            warmup_frames: int = WARMUP_FRAMES,
            duration: float = BENCHMARK_DURATION,
            ) -> None:
        self.video_path = video_path or BENCHMARK_VIDEO_PATH
        self.person_model_path = person_model_path or PERSON_MODEL_PATH
        self.venv_python = venv_python or get_venv_python()
        self.warmup_frames = warmup_frames
        self.duration = duration

    def video_is_available(self) -> bool:
        """Checks whether test clip exists"""
        return self.video_path.is_file()

    @staticmethod
    def _rate_fps(avg_fps: float) -> str:
        """Classifies sustained fps into good/limited/insufficient ratings"""
        if avg_fps >= MIN_FPS_PER_CAMERA_GOOD:
            return RATING_GOOD
        if avg_fps >= MIN_FPS_PER_CAMERA_LIMITED:
            return RATING_LIMITED
        return RATING_INSUFFICIENT

    def _parse_progress_line(self, line: str) -> tuple[str, float] | None:
        """Parses a 'PROGRESS:<message>|<fraction>' line from the runner"""
        _, _, rest = line.partition(":")
        message, sep, fraction = rest.rpartition("|")

        if not sep:
            return None

        try:
            return message, float(fraction)
        except ValueError:
            return None

    def run(self, progress_callback: ProgressCallback | None = None) -> BenchmarkResult:#NOSONAR
        """
        Launches the benchmark runner script under the venv Python interpreter,
        streams its progress back through progress_callback and returns BenchmarkResult

        progress_callback receives message and fraction 
        and is used to update gui status label and progress bar during run
        Safe to call from a backgorund thread - it does not touch Tkinter
        """
        def report(message: str, fraction: float) -> None:
            if progress_callback is not None:
                progress_callback(message, fraction)

        if not self.video_is_available():
            return BenchmarkResult(
                error=f"Benchmark clip not found: {self.video_path}"
            )

        if is_packaged():
            service_executable = get_service_executable()

            if not service_executable.is_file():
                return BenchmarkResult(
                    error=(
                        "The packaged WatchDog AI service could not be found. "
                        "Please reinstall WatchDog."
                    )
                )

            command = [
                str(service_executable),
                "--benchmark",
                "--video",
                str(self.video_path),
                "--model",
                str(self.person_model_path),
                "--warmup-frames",
                str(self.warmup_frames),
                "--duration",
                str(self.duration),
            ]

        else:
            if not self.venv_python.is_file():
                return BenchmarkResult(
                    error=(
                        "WatchDog's Python environment could not be found. "
                        "Please complete the dependency setup first."
                    )
                )

            command = [
                str(self.venv_python),
                str(RUNNER_SCRIPT_PATH),
                "--video",
                str(self.video_path),
                "--model",
                str(self.person_model_path),
                "--warmup-frames",
                str(self.warmup_frames),
                "--duration",
                str(self.duration),
            ]

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as error:
            return BenchmarkResult(
                error=f"Could not start benchmark process: {error}"
            )

        payload: dict | None = None

        assert process.stdout is not None
        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("PROGRESS:"):
                parsed = self._parse_progress_line(line)
                if parsed is not None:
                    report(*parsed)
            elif line.startswith("RESULT:"):
                _, _, raw_json = line.partition(":")
                try:
                    payload = json.loads(raw_json)
                except ValueError:
                    payload = {"error": "Could not parse benchmark results."}

        stderr_output = process.stderr.read() if process.stderr else ""
        process.wait()

        if payload is None:
            detail = stderr_output.strip() or f"exit code {process.returncode}"
            return BenchmarkResult(error=f"Benchmark process failed: {detail}")

        if payload.get("error"):
            return BenchmarkResult(error=str(payload["error"]))

        result = BenchmarkResult(
            frames_processed=payload.get("frames_processed", 0),
            duration=payload.get("duration", 0.0),
            avg_fps=payload.get("avg_fps", 0.0),
            p95_frame_time=payload.get("p95_frame_time", 0.0),
            peak_memory=payload.get("peak_memory", 0.0),
            peak_cpu_percent=payload.get("peak_cpu_percent", 0.0),
            gpu_available=payload.get("gpu_available", False),
            gpu_name=payload.get("gpu_name"),
            peak_gpu_memory=payload.get("peak_gpu_memory", 0.0),
        )
        result.rating = self._rate_fps(result.avg_fps)
        return result

def estimate_max_cameras(
        avg_fps: float,
        target_fps_per_camera: float = MIN_FPS_PER_CAMERA_GOOD,
) -> int:
    """
    Rough estimate of how many concurrent camera streams user machine could sustain 
    based on single stream throughput
    This is not a gurantee, rather an optimistic upper bound
    """
    if target_fps_per_camera <= 0:
        return 0

    return max(int(avg_fps // target_fps_per_camera), 0)