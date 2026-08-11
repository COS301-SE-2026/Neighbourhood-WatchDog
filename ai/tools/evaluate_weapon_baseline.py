"""
Evaluate the current WatchDog threat model against the frozen Gun/knife dataset.

Run from ai/:
    python tools/evaluate_weapon_baseline.py
"""


from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from ultralytics import YOLO
from evaluation.metrics import Detection, score_class
import argparse
import csv
import hashlib
import json
import cv2


AI_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = AI_ROOT / "data/curated/weapons-gun-knife-v1/dataset"
DEFAULT_MODEL = AI_ROOT / "pipeline/models/weights/best.pt"
DEFAULT_REPORT = AI_ROOT / "evaluation/reports/weapon-baseline-v1"
DATASET_CLASSES = {0: "Gun", 1: "knife"}
MODEL_TO_DATASET = {0: 0, 3: 1}


def sha256(path: Path) -> str:
    """hashing calc"""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def read_labels(path: Path, width: int, height: int) -> list[Detection]:
    """reads yolo txt annotation file"""

    records: list[Detection] = []

    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue

        fields = line.split()

        if len(fields) != 5:
            raise ValueError(f"{path}:{number}: expected five YOLO fields")

        class_id = int(fields[0])

        if class_id not in DATASET_CLASSES:
            raise ValueError(f"{path}:{number}: unexpected dataset class {class_id}")

        cx, cy, bw, bh = (float(value) for value in fields[1:])

        records.append(Detection(
            bbox_xyxy=((cx - bw / 2) * width, (cy - bh / 2) * height, (cx + bw / 2) * width, (cy + bh / 2) * height),
            confidence=1.0
        ))

        

    return records