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