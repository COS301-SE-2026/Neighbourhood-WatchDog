from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import psutil

from dependency_service import AI_DIR, PERSON_MODEL_PATH
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
MIN_FPS_PER_CAMERA_MARGINAL = 6.0 #6-10 -> usable, but tight

RATING_GOOD = "good"
RATING_MARGINAL = "marginal"
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
        """Classifies sustained fps into good/marginal/insufficient ratings"""
        if avg_fps >= MIN_FPS_PER_CAMERA_GOOD:
            return RATING_GOOD
        if avg_fps >= MIN_FPS_PER_CAMERA_MARGINAL:
            return RATING_MARGINAL
        return RATING_INSUFFICIENT
        