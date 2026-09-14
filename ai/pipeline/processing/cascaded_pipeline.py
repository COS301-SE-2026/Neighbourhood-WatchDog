"""
1) Human detection on the full frame
2) Threat detection only after each human crop
3) DEEPSORT tracking of person detections
4) Zone based behaviour classification using in-memory track history


"""

from __future__ import annotations
from collections import dataclass, field
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


