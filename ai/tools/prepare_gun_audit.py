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
