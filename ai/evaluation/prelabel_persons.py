"""Create review-only YOLO person-label drafts for the compact WatchDog evaluation set.

This script uses the same person model being evaluated, so its output is NEVER ground
truth by itself. Open every generated label in LabelImg and correct missed, extra, or
badly placed boxes before running the baseline.

Run from ai/ after extract_eval_frames.py:
    python evaluation/prelabel_persons.py --conf 0.25
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from tools.security import _resolve_within, _safe_frame_id

import cv2
from ultralytics import YOLO

AI_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = AI_ROOT / "evaluation"
MANIFEST_PATH = EVALUATION_DIR / "dataset_manifest.csv"
LABELS_DIR = EVALUATION_DIR / "labels"
PERSON_MODEL_PATH = AI_ROOT / "pipeline" / "models" / "weights" / "yolov8n.pt"


def is_person_positive_candidate(source_file: str) -> bool:
    """Select known presence assets, never no_presence controls."""
    source_file = source_file.lower()
    return "presence" in source_file and "no_presence" not in source_file


def to_yolo_line(x1: float, y1: float, x2: float, y2: float, width: int, height: int) -> str | None:
    x1, x2 = sorted((max(0.0, x1), min(float(width), x2)))
    y1, y2 = sorted((max(0.0, y1), min(float(height), y2)))
    box_width, box_height = x2 - x1, y2 - y1
    if box_width <= 0 or box_height <= 0:
        return None
    x_center = (x1 + x2) / 2 / width
    y_center = (y1 + y2) / 2 / height
    return f"0 {x_center:.6f} {y_center:.6f} {box_width / width:.6f} {box_height / height:.6f}"

def main() -> None:
    parser = argparse.ArgumentParser(description="Create review-only person label drafts.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--labels-dir", type=Path, default=LABELS_DIR)
    parser.add_argument("--conf", type=float, default=0.25, help="Person-model confidence threshold.")
    parser.add_argument("--overwrite", action="store_true", help="Replace reviewed label files. Use only deliberately.")
    args = parser.parse_args()

    if not 0 < args.conf <= 1:
        parser.error("--conf must be greater than 0 and no more than 1")
    if not args.manifest.exists():
        parser.error(f"Manifest not found: {args.manifest}. Run extract_eval_frames.py first.")

    with args.manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    candidates = [row for row in rows if is_person_positive_candidate(row["source_file"])]
    args.labels_dir = _resolve_within(EVALUATION_DIR, args.labels_dir, "--labels-dir")
    args.labels_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(PERSON_MODEL_PATH)
    created = skipped = empty_drafts = 0
    for row in candidates:
        frame_id = _safe_frame_id(row["frame_id"])
        label_path = args.labels_dir / f"{frame_id}.txt"
        if label_path.exists() and not args.overwrite:
            skipped += 1
            print(f"SKIP existing label (preserve human work): {label_path.name}")
            continue

        image_path = AI_ROOT / row["frame_path"]
        image = cv2.imread(str(image_path))
        if image is None:
            raise RuntimeError(f"Cannot read manifest image: {image_path}")
        height, width = image.shape[:2]

        result = model.predict(image, imgsz=640, conf=args.conf, classes=[0], verbose=False)[0]
        lines: list[str] = []
        for box in result.boxes:
            line = to_yolo_line(*(float(value) for value in box.xyxy[0].tolist()), width, height)
            if line:
                lines.append(line)
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        created += 1
        if not lines:
            empty_drafts += 1
        print(f"DRAFT {label_path.name}: {len(lines)} predicted person box(es)")

    print(f"Created {created} review-only draft labels; skipped {skipped} existing labels.")
    if empty_drafts:
        print(f"WARNING: {empty_drafts} known presence item(s) received no prediction; add person boxes manually.")
    print("Review every DRAFT in LabelImg before treating it as ground truth.")


if __name__ == "__main__":
    main()
