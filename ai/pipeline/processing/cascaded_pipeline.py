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


class CascadedPipeline:
    """running the local stages for one camera"""

    def __init__(self, *, person_model: Any, weapon_model: Any, 
                 zones: Sequence[Sequence[Sequence[float]]] = (), 
                 zone_ids: Sequence[str] = (), config: CascadedPipelineConfig | None = None, 
                 tracker: Any | None = None, inference_lock: Lock | None = None) -> None:
        
        self.person_model = person_model
        self.weapon_model = weapon_model
        self.zones = tuple(tuple(tuple(point) for point in polygon) for polygon in zones)
        self.zone_ids = tuple(str(value) for value in zone_ids)
        self.config = config or CascadedPipelineConfig()
        self.inference_lock = inference_lock

        if tracker is not None:
            self.tracker = tracker
        else:
            if DeepSort is None:
                raise RuntimeError("deep-sort-realtime is required unless a tracker is injected")

            self.tracker = DeepSort(
                max_age=self.config.max_age, 
                n_init=self.config.n_init, 
                max_iou_distance=self.config.max_iou_distance,
                embedder="mobilenet",
                embedder_gpu=False,
                nms_max_overlap=0.5,
            )

        self._histories: dict[int, _TrackHistory] = {}

    
