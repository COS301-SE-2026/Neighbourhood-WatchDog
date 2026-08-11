"""
Final YOLO dataset for detecting two classes: Gun and knife
"""

from __future__ import annotations
from collections import Counter
from pathlib import Path
import argparse
import csv
import shutil


AI_ROOT = Path(__file__).resolve().parents[1]
AUDIT_CSV = AI_ROOT / "data/curated/weapons-gun-knife-v1/audit/gun_review.csv"
WEAPON_SOURCE = AI_ROOT / "data/external/cctv-weapon-dataset/Dataset"
KNIFE_SOURCE = AI_ROOT / "data/external/cctv-knife-detection-dataset/Knife_Dataset"
DEFAULT_OUTPUT = AI_ROOT / "data/curated/weapons-gun-knife-v1/dataset"


GUN_SCENE_SPLITS = {
    "Scene1": "train",
    "Scene2": "evaluation",
    "Scene3": "train",
    "Scene4": "train",
    "Scene5": "train",
    "Scene6": "validation",
}

KNIFE_SPLITS = {
    "train": range(1, 70),
    "validation": range(70, 85),
    "evaluation": range(85, 115),
}


def parse_yolo(path: Path) -> list[tuple[int, float, float, float, float]]:
    """reads in yolo annotation file"""

    records = []

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

        records.append((class_id, *values))


    return records