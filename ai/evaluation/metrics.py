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

 