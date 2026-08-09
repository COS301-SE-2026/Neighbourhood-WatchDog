"""
This script builds a fixed evaluation dataset from your WatchDog test videos and images. 
It extracts selected video frames, copies the still images into the evaluation folder, and creates a CSV manifest describing every evaluation image.
"""

from future import annotations
from pathlib import Path
import argparse
import csv
import cv2
import numpy as np


AI_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = AI_ROOT / "evaluation"
FRAMES_DIR =  EVALUATION_DIR / "frames"
MANIFEST_PATH = EVALUATION_DIR / "dataset_manifest.csv"
FOOTAGE_DIR = AI_ROOT / "tests" / "footage"
IMAGE_DIR = AI_ROOT / "tests" / "image"



