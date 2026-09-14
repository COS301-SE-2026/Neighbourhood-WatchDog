"""
1) Human detection on the full frame
2) Threat detection only after each human crop
3) DEEPSORT tracking of person detections
4) Zone based behaviour classification using in-memory track history


"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Sequence

import time


try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except ImportError: # pragma: no cover
    DeepSort = None # type: ignore[assignment]



PERSON_CLASS_ID = 0
DETECTION_HUMAN = "HUMAN_PRESENCE"
DETECTION_LOITERING = "LOITERING"
DETECTION_PERIMETER_SCAN = "PERIMETER_SCAN"
DETECTION_WEAPON = "WEAPON_DETECTED"

SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class CascadedPipelineConfig:

    person_confidence: float = 0.25
    person_iou: float = 0.70
    person_imgsz: int = 640
    weapon_confidence: float = 0.50
    weapon_iou: float = 0.50
    weapon_imgsz: int = 512
    max_age: int = 10
    n_init: int = 3
    max_iou_distance: float = 0.5
    loitering_threshold_seconds: float = 30.0
    scan_time_window_seconds: float = 30.0
    scan_crossing_threshold: int = 3
    history_retention_seconds: float = 300.0


@dataclass
class PipelineResult:
    tracks: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    


@dataclass
class _TrackHistory:

    last_seen: float = 0.0
    previous_inside: tuple[bool, ...] | None = None
    entered_at: dict[int, float] = field(default_factory=dict)
    crossings: dict[int, deque[float]] = field(default_factory=dict)
    last_emitted_type: str | None = None