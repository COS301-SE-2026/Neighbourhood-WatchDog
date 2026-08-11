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

def write_yolo(path: Path, records: list[tuple[int, float, float, float, float]]) -> None:
    """python annotations converted into yolo format"""

    path.write_text("".join(f"{class_id} {cx:.6f} {cy:.6f} {width:.6f} {height:.6f}\n" for class_id, cx, cy, width, height in records), encoding="utf-8")


def knife_split(image_name: str) -> str:
    """determines which split a knife image belongs to"""

    prefix = "Knife_scenario_"

    if not image_name.startswith(prefix) or not image_name.endswith(".png"):
        raise ValueError(f"Unexpected knife filename: {image_name}")

    number = int(image_name[len(prefix):-4])

    for split, numbers in KNIFE_SPLITS.items():
        if number in numbers:
            return split

    raise ValueError(f"Knife filename is outside the expected 1..114 range: {image_name}")

def prepare_output(output: Path, overwrite: bool) -> None:
    """output dataset directories"""

    if output.exists():
        if not overwrite:
            raise FileExistsError(f"Output already exists: {output}. Review it or pass --overwrite deliberately.")
        shutil.rmtree(output)

    for split in ("train", "validation", "evaluation"):
        (output / split / "images").mkdir(parents=True, exist_ok=True)
        (output / split / "labels").mkdir(parents=True, exist_ok=True)


def copy_item(image: Path, labels: list[tuple[int, float, float, float, float]],split: str, destination: Path, name:str) -> None:
    """copies one image and creates its corresponding label."""

    image_destination = destination / split / "images" / name
    label_destination = destination / split / "labels" / f"{Path(name).stem}.txt"
    shutil.copy2(image, image_destination)
    write_yolo(label_destination, labels)