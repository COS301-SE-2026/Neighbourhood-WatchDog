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
