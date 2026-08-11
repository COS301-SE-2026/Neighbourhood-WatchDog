"""
CSV generation for a reviewer to retain clear firearm examples

Run from ai/:
    python tools/prepare_gun_audit.py

"""

from __future__ import annotations
from pathlib import Path
import argparse
import csv
import re
import shutil
import cv2

AI_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = AI_ROOT / "data/external/cctv-weapon-dataset/Dataset"
DEFAULT_AUDIT_DIR = AI_ROOT / "data/curated/weapons-gun-knife-v1/audit"


CSV_FIELDS = ["source_image", "source_label", "scene_group", "weapon_box_count", "decision", "reason", "assigned_split"]


def parse_yolo(path: Path) -> list[tuple[int, float, float, float, float]]:
    """reads in yolo annotation file"""

    boxes: list[tuple[int, float, float, float, float]] = []

    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue

        fields = line.split()

        if len(fields) != 5:
            raise ValueError(f"{path}:{number}: expected 5 YOLO fields")

        class_id = int(fields[0])
        values = tuple(float(value) for value in fields[1:])

        if not all(0.0 <= value <= 1.0 for value in values):
            raise ValueError(f"{path}:{number}: normalized values must be in [0,1]")

        boxes.append(class_id, *values)


    return boxes