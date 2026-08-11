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

        boxes.append((class_id, *values))


    return boxes


def scene_group(image_name: str) -> str:
    """extracts scene identifier from an image filename"""

    match = re.match(r"^(Scene\d+)_", image_name)

    if not match:
        raise ValueError(f"Cannot derive source scene from {image_name}")

    return match.group(1)


def draw_preview(image_path: Path, label_path: Path, destination: Path) -> None:
    """creates a visual copy of the image with the generic weapon bounding boxes drawn on it."""

    image = cv2.imread(str(image_path))

    if image is None:
        raise RuntimeError(f"Cannot read image: {image_path}")

    height, width = image.shape[:2]

    for class_id, cx, cy, bw, bh in parse_yolo(label_path):
        if class_id != 1:
            continue

        x1 = max(0, round((cx - bw / 2) * width))
        y1 = max(0, round((cy - bh / 2) * height))
        x2 = min(width - 1, round((cx + bw / 2) * width))
        y2 = min(height - 1, round((cy + bh / 2) * height))

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(image, "generic weapon - REVIEW", (x1, max(25, y1 - 8)), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

        max_width = 900

        if width > max_width:
            scale = max_width / width
            image = cv2.resize(image, (round(width * scale), round(height * scale)))

    cv2.imwrite(str(destination), image)