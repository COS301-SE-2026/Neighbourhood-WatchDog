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
