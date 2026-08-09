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


VIDEO_FILES = ("blurred-no_presence.mp4", "blurred-presence.mp4", "clear-no_presence.mp4", "clear-presence.mp4")
IMAGE_FILES = ("blurred-presence-multi.jpg", "blurred-presence.jpg", "clear-presence-multi.jpg", "clear-presence.jpg")
MANIFEST_COLUMNS = (
    "frame_id",
    "source_file",
    "frame_number",
    "timestamp_seconds",
    "frame_path",
    "width",
    "height",
    "split"

)

def frame_id_for(stem: str, frame_number:int) -> str:
    return f"{stem}_f{frame_number:06d}" #frame number is always going to be 6 digits

def extract_video_frames(video_path: Path, samples_per_video:int, force: bool) -> list[dict[str, str | int | float]]:

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")


    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if frame_count <= 0  or fps <= 0:
        capture.release()
        raise RuntimeError(f"Invalid frame count or fps for {video_path}: {frame_count}/{fps}")


    selected = np.linspace(0, frame_count - 1, num=min(samples_per_video, frame_count), dtype=int)
    rows: list[dict[str, str | int | float]] = []
    for number in sorted(set(int(value) for value in selected)):
        capture.set(cv2.CAP_PROP_POS_FRAMES, number)
        ok, frame = capture.read()

        if not ok or frame is None:
            capture.release()
            raise RuntimeError(f"Could not rad frame {number} from {video_path}")

        frame_id = frame_id_for(video_path.stem, number)
        output = FRAMES_DIR / f"{frame_id}.jpg"

        if force or not output.exists():
            if not cv2.imwrite(str(output), frame):
                capture.release()
                raise RuntimeError(f"Could not write {output}")

        height, width = frame.shape[:2]
        rows.append({
            "frame_id": frame_id,
            "source_file": str(video_path.relative_to(AI_ROOT)).replace("\\", "/"),
            "frame_number": number,
            "timestamp_seconds": round(number / fps, 6),
            "frame_path": str(output.relative_to(AI_ROOT)).replace("\\", "/"),
            "width": width,
            "height": height,
            "split": "evaluation"
        })

        capture.release()
        return rows


def add_still_images() -> list[dict[str, str | int | float]]:
    rows: list[dict[str, str | int | float]] = []

    for filename in IMAGE_FILES:
        source = IMAGE_DIR / filename
        image = cv2.imread(str(source))

        if image is None:
            raise RuntimeError(f"Cannot read image: {source}")

        frame_id = source.stem
        output = FRAMES_DIR / f"{frame_id}.jpg"

        if not output.exists() and not cv2.imwrite(str(output), image):
            raise RuntimeError(f"Could not write {output}")

        height, width = image.shape[:2]
        rows.append({
            "frame_id": frame_id,
            "source_file": str(source.relative_to(AI_ROOT)).replace("\\", "/"),
            "frame_number": "",
            "timestamp_seconds": "",
            "frame_path": str(output.relative_to(AI_ROOT)).replace("\\", "/"),
            "width": width,
            "height": height,
            "split": "evaluation",
        })
    return rows