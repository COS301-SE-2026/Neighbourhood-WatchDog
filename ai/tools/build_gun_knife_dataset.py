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
