from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import psutil

from dependency_service import AI_DIR, PERSON_MODEL_PATH

try:
    import torch
except ImportError:
    torch = None