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


def score_class(predictions: Iterable[Detection], ground_truth: Iterable[Detection], iou_threshold: float = 0.50) -> dict[str, object]:
    """Greedily match confidence-sorted predictions to one ground-truth box each."""

    predictions = sorted(predictions, key=lambda item: item.confidence, reverse=True)
    ground_truth = list(ground_truth)

    unmatched_truth = set(range(len(ground_truth)))
    matched_pairs: list[tuple[int, int, float]] = []
    false_positive_indices: list[int] = []

    for prediction_index, prediction in enumerate(predictions):
        candidates = [
            (truth_index, iou_xyxy(prediction.bbox_xyxy, ground_truth[truth_index].bbox_xyxy))
            for truth_index in unmatched_truth
        ]

        if not candidates:
            false_positive_indices.append(prediction_index)
            continue

        truth_index, best_iou = max(candidates, key=lambda item: item[1])

        if best_iou >= iou_threshold:
            unmatched_truth.remove(truth_index)
            matched_pairs.append((prediction_index, truth_index, best_iou))
        else:
            false_positive_indices.append(prediction_index)

    tp = len(matched_pairs)
    fp = len(false_positive_indices)
    fn = len(unmatched_truth)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "matched_pairs": matched_pairs,
        "false_positive_indices": false_positive_indices,
        "false_negative_indices": sorted(unmatched_truth)
    }