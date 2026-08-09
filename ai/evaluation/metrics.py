"""
This code takes the model's predictions and the human-created ground-truth labels and determines:

True Positives (TP)
False Positives (FP)
False Negatives (FN)
Precision
Recall
F1-score
Which prediction matched which ground-truth object

"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Detection:
    class_id: int
    bbox_xyxy: tuple[float, float, float, float]
    confidence: float = 1.0

def iou_xyxy(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    """Return intersection-over-union for two (x1, y1, x2, y2) boxes."""

    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_w, inter_h = max(0.0, inter_x2 - inter_x1), max(0.0, inter_y2 - inter_y1)

    intersection = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    union = area_a + area_b - intersection
    
    return intersection / union if union > 0 else 0.0