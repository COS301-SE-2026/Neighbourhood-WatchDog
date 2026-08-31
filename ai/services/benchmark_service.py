from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import psutil

from services.dependency_service import AI_DIR, PERSON_MODEL_PATH
from pipeline.processing.tracker import Detector

try:
    import torch
except ImportError:
    torch = None

ASSETS_DIR = AI_DIR / "assets"
BENCHMARK_VIDEO_PATH = ASSETS_DIR / "clear-presence.mp4"

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
            warmup_frames: int = WARMUP_FRAMES,
            duration: float = BENCHMARK_DURATION,
            ) -> None:
        self.video_path = video_path or BENCHMARK_VIDEO_PATH
        self.person_model_path = person_model_path or PERSON_MODEL_PATH
        self.warmup_frames = warmup_frames
        self.duration = duration
        self._process = psutil.Process()

    def video_is_available(self) -> bool:
        """Checks whether test clip exists"""
        return self.video_path.is_file()

    def _detect_gpu(self) -> tuple[bool, str | None]:
        """Checks whether torch can see a usable CUDA device"""
        if torch is None:
            return False, None

        try:
            if torch.cuda.is_available():
                return True, torch.cuda.get_device_name(0)
        except Exception:
            pass

        return False, None

    @staticmethod
    def _rate_fps(avg_fps: float) -> str:
        """Classifies sustained fps into good/limited/insufficient ratings"""
        if avg_fps >= MIN_FPS_PER_CAMERA_GOOD:
            return RATING_GOOD
        if avg_fps >= MIN_FPS_PER_CAMERA_LIMITED:
            return RATING_LIMITED
        return RATING_INSUFFICIENT

    def _run_warmup(self, detector: Detector, capture: cv2.VideoCapture) -> None:
        """
        Feeds first few frames through pipeline without timing them
        so that loading the model and starting GPU doesn't skew the results
        """
        for _ in range(self.warmup_frames):
            ok, frame = capture.read()
            if not ok:
                break

            detector.process_frame(frame)

    def _run_measured(
            self,
            detector: Detector,
            capture: cv2.VideoCapture,
            report: Callable[[str, float], None]
    ) -> tuple[list[float], float, float, float]:
        """
        Runs detector against clip and records per-frame timings
        and peak CPU, memory and VRAM usage along the way
        """
        frame_times: list[float] = []
        peak_memory = 0.0
        peak_cpu_percent = 0.0
        peak_gpu_memory = 0.0

        self._process.cpu_percent(interval=None)

        start_time = time.monotonic()

        while (time.monotonic() - start_time) < self.duration:
            ok, frame = capture.read()

            if not ok:
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame_start = time.perf_counter()
            detector.process_frame(frame)
            frame_times.append(time.perf_counter() - frame_start)

            peak_memory = max(
                peak_memory,
                self._process.memory_info.rss / (1024 * 1024),
            )

            peak_cpu_percent = max(
                peak_cpu_percent,
                self._process.cpu_percent(interval=None),
            )

            if torch is not None and torch.cuda.is_available():
                peak_gpu_memory = max(
                    peak_gpu_memory,
                    torch.cuda.max_memory_allocated() / (1024 * 1024),
                )

            elapsed_fraction = (time.monotonic() - start_time / self.duration)

            report(
                "Measuring performance...",
                min(0.2 + elapsed_fraction * 0.8, 0.99),
            )

            return frame_times, peak_memory, peak_cpu_percent, peak_gpu_memory

    def _build_result(
            self,
            *,
            frame_times: list[float],
            peak_memory: float,
            peak_cpu_percent: float,
            gpu_available: bool,
            gpu_name: str | None,
            peak_gpu_memory: float,
    ) -> BenchmarkResult:
        """Turns per-frame timings into summarised result"""
        frames_processed = len(frame_times)
        duration = sum(frame_times)
        avg_fps = frames_processed / duration if duration > 0 else 0.0
        sorted_times = sorted(frame_times)
        p95_index = min(int(len(sorted_times) * 0.95), len(sorted_times) - 1)
        p95_frame_time = sorted_times[p95_index] * 1000 #milliseconds

        return BenchmarkResult(
            frames_processed=frames_processed,
            duration=duration,
            avg_fps=avg_fps,
            p95_frame_time=p95_frame_time,
            peak_memory=peak_memory,
            peak_cpu_percent=peak_cpu_percent,
            gpu_available=gpu_available,
            gpu_name=gpu_name,
            peak_gpu_memory=peak_gpu_memory,
            rating=self._rate_fps(avg_fps),
        )

    def run(self, progress_callback: ProgressCallback | None = None) -> BenchmarkResult:
        """
        Runs a warmup pass then a measured pass of the detector over the test clip
        and returns benchmark results.

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
        
        try:
            report("Loading detection model...", 0.0)
            detector = Detector(str(self.person_model_path))
        except Exception as error:
            return BenchmarkResult(error=f"Could not load model: {error}")

        gpu_available, gpu_name = self._detect_gpu()

        capture = cv2.VideoCapture(str(self.video_path))
        if not capture.isOpened():
            return BenchmarkResult(
                error=f"Could not open benchmark clip: {self.video_path}"
            )

        try:
            report("Warming up...", 0.05)
            self._run_warmup(detector, capture)

            report("Measuring performance...", 0.2)
            frame_times, peak_memory, peak_cpu_percent, peak_gpu_memory = (
                self._run_measured(detector, capture, report)
            )
        finally:
            capture.release()

        if not frame_times:
            return BenchmarkResult(
                error="Benchmark clip ended before any frames could be measured."
            )

        result = self._build_result(
            frame_times=frame_times,
            peak_memory=peak_memory,
            peak_cpu_percent=peak_cpu_percent,
            gpu_available=gpu_available,
            gpu_name=gpu_name,
            peak_gpu_memory=peak_gpu_memory,
        )

        report("Benchmark complete", 1.0)
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