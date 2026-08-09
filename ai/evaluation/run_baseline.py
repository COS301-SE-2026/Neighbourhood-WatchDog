"""Run a fixed, offline baseline evaluation for WatchDog person/threat detection.

Run from ai/ after every manifest item has a human-reviewed YOLO label file:
    python -m evaluation.run_baseline --weapon-conf 0.50

This program intentionally does not import app.py, start DeepSort, call the backend,
or create alerts. It measures raw model detection accuracy only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import cv2
from ultralytics import YOLO

from evaluation.metrics import Detection, score_class

AI_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = AI_ROOT / "evaluation"
MANIFEST_PATH = EVALUATION_DIR / "dataset_manifest.csv"
LABELS_DIR = EVALUATION_DIR / "labels"
PERSON_MODEL_PATH = AI_ROOT / "pipeline" / "models" / "weights" / "yolov8n.pt"
THREAT_MODEL_PATH = AI_ROOT / "pipeline" / "models" / "weights" / "best.pt"

CLASS_NAMES = {0: "person", 1: "Gun", 2: "explosion", 3: "grenade", 4: "knife"}
# best.pt IDs -> shared evaluation IDs. This is based on the verified model names:
# {0: 'Gun', 1: 'explosion', 2: 'grenade', 3: 'knife'}
THREAT_MODEL_TO_EVALUATION_CLASS = {0: 1, 1: 2, 2: 3, 3: 4}
WEAPON_CLASS_IDS = frozenset({1, 2, 3, 4})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def yolo_to_xyxy(values: list[float], width: int, height: int) -> tuple[float, float, float, float]:
    _, x_center, y_center, box_width, box_height = values
    x_center, box_width = x_center * width, box_width * width
    y_center, box_height = y_center * height, box_height * height

    return (
        x_center - box_width / 2,
        y_center - box_height / 2,
        x_center + box_width / 2,
        y_center + box_height / 2,
    )


def read_ground_truth(label_path: Path, width: int, height: int) -> list[Detection]:
    """Read a YOLO label file. An existing empty file is an intentional negative."""

    if not label_path.exists():
        raise FileNotFoundError(
            f"Missing human ground-truth label: {label_path}. Create an empty file for a confirmed negative frame."
        )
    
    detections: list[Detection] = []

    for line_number, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue

        parts = raw_line.split()

        if len(parts) != 5:
            raise ValueError(f"{label_path}:{line_number}: expected 5 YOLO values, got {len(parts)}")
        
        values = [float(value) for value in parts]

        class_id = int(values[0])

        if class_id not in CLASS_NAMES:
            raise ValueError(f"{label_path}:{line_number}: unknown class ID {class_id}")

        if not all(0.0 <= value <= 1.0 for value in values[1:]):
            raise ValueError(f"{label_path}:{line_number}: YOLO coordinates must be between 0 and 1")

        detections.append(Detection(class_id=class_id, bbox_xyxy=yolo_to_xyxy(values, width, height)))

    return detections


def predict(frame, person_model: YOLO, threat_model: YOLO, person_confidence: float, weapon_confidence: float) -> list[Detection]:

    predictions: list[Detection] = []

    person_results = person_model.predict(
        frame, 
        imgsz=640, 
        conf=person_confidence, 
        classes=[0], 
        verbose=False
    )

    for box in person_results[0].boxes:
        predictions.append(Detection(
            class_id=0,
            bbox_xyxy=tuple(float(value) for value in box.xyxy[0].tolist()),
            confidence=float(box.conf[0]),
        ))

    threat_results = threat_model.predict(frame, 
                                          imgsz=512, 
                                          conf=weapon_confidence, 
                                          verbose=False
                                          )
    
    for box in threat_results[0].boxes:
        threat_class_id = int(box.cls[0])

        if threat_class_id not in THREAT_MODEL_TO_EVALUATION_CLASS:
            raise ValueError(f"Unexpected best.pt class ID {threat_class_id}; update the evaluation mapping.")

        predictions.append(Detection(
            class_id=THREAT_MODEL_TO_EVALUATION_CLASS[threat_class_id],
            bbox_xyxy=tuple(float(value) for value in box.xyxy[0].tolist()),
            confidence=float(box.conf[0]),
        ))
        
    return predictions
