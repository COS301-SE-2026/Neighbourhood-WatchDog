"""Tune person confidence and YOLO NMS (non maximum suppression) IoU against the fixed WatchDog evaluation set.

The script evaluates raw person detections only. It does not change app.py, model weights,
DeepSort, or alerts. Use the selected values only after reviewing tuning_results.csv.

Run from ai/:
    python -m evaluation.tune_person_detector --min-recall 0.966667
"""


from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from ultralytics import YOLO
from evaluation.metrics import Detection, score_class
from evaluation.run_baseline import AI_ROOT, LABELS_DIR, MANIFEST_PATH, PERSON_MODEL_PATH, read_ground_truth, sha256
import argparse
import csv
import json
import cv2


DEFAULT_CONFIDENCES = (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
DEFAULT_NMS_IOUS = (0.40, 0.45, 0.50, 0.55, 0.60)


def parse_values(value: str) -> tuple[float, ...]:
    """convert command line string into tuple of floats"""

    values = tuple(float(item.strip()) for item in value.split(",") if item.strip())

    if not values or not all(0.0 < item <= 1.0 for item in values):
        raise argparse.ArgumentTypeError("Provide one or more comma separated values in (0, 1].")

    return values


def evaluate_candidate(manifest: list[dict[str, str]], labels_dir: Path, model: YOLO, confidence:float, nms_iou: float, match_iou: float) -> dict[str, float | int]:
    """evaluates combination of person detector settings against watchdog evaluation dataset"""

    counts = defaultdict(int)

    for row in manifest:
        frame = cv2.imread(str(AI_ROOT / row["frame_path"]))
        if frame is None:
            raise RuntimeError(f"Cannot read evaluation frame: {row['frame_path']}")

        height, width = frame.shape[:2]

        ground_truth = [item for item in read_ground_truth(labels_dir / f"{row['frame_id']}.txt", width, height) if item.class_id == 0]

        result = model.predict(
            frame, 
            imgsz=640, 
            conf=confidence, 
            iou=nms_iou, 
            classes=[0], 
            verbose=False
        )[0]
        predictions = [
            Detection(
                class_id=0, 
                bbox_xyxy=tuple(float(value) for value in box.xyxy[0].tolist()),
                confidence=float(box.conf[0])
            ) for box in result.boxes
        ]

        score = score_class(predictions, ground_truth, match_iou)
        for key in ("tp", "fp", "fn"):
            counts[key] += int(score[key])

        tp = counts["tp"]
        fp = counts["fp"]
        fn = counts["fn"]

        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0

        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

        return{
            "person_confidence": confidence, 
            "person_nms_iou": nms_iou, 
            "tp": tp, 
            "fp": fp, 
            "fn": fn, 
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6)
        }