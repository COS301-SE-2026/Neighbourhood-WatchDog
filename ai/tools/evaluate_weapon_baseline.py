"""
Evaluate the current WatchDog threat model against the frozen Gun/knife dataset.

Run from ai/:
    python tools/evaluate_weapon_baseline.py
"""

from __future__ import annotations


import argparse
import csv
import hashlib
import json
import cv2

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from ultralytics import YOLO
from evaluation.metrics import Detection, score_class
from tools.security import _resolve_within


AI_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = AI_ROOT / "data/curated/weapons-gun-knife-v1/dataset"
DEFAULT_MODEL = AI_ROOT / "pipeline/models/weights/best.pt"
DEFAULT_REPORT = AI_ROOT / "evaluation/reports/weapon-baseline-v1"
DATASET_CLASSES = {0: "Gun", 1: "knife"}
MODEL_TO_DATASET = {0: 0, 3: 1}


def sha256(path: Path) -> str:
    """hashing calc"""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def read_labels(path: Path, width: int, height: int) -> list[Detection]:
    """reads yolo txt annotation file"""

    records: list[Detection] = []

    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue

        fields = line.split()

        if len(fields) != 5:
            raise ValueError(f"{path}:{number}: expected five YOLO fields")

        class_id = int(fields[0])

        if class_id not in DATASET_CLASSES:
            raise ValueError(f"{path}:{number}: unexpected dataset class {class_id}")

        cx, cy, bw, bh = (float(value) for value in fields[1:])

        records.append(Detection(
            class_id=class_id,
            bbox_xyxy=((cx - bw / 2) * width, (cy - bh / 2) * height, (cx + bw / 2) * width, (cy + bh / 2) * height),
            confidence=1.0
        ))



    return records


def summary(counts: dict[str, int]) -> dict[str, int | float | str]:
    """calc precsion, recall, f1"""

    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        **counts,
        "ground_truth_count": tp + fn,
        "prediction_count": tp + fp,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "status": "measurable" if tp + fn else "not_measurable_no_ground_truth_positive"
    }


def main() -> None:

    parser = argparse.ArgumentParser(description="Measure the current threat model on frozen Gun/knife evaluation data.")

    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--confidence", type=float, default=0.50)
    parser.add_argument("--nms-iou", type=float, default=0.50)
    parser.add_argument("--match-iou", type=float, default=0.50)

    args = parser.parse_args()

    args.dataset = _resolve_within(AI_ROOT, args.dataset, "--dataset")
    args.model = _resolve_within(AI_ROOT, args.model, "--model")
    args.report_dir = _resolve_within(AI_ROOT, args.report, "--report")

    if not all(0.0 < value <= 1.0 for value in (args.confidence, args.nms_iou, args.match_iou)):
        parser.error("confidence and IoU values must be in (0, 1]")

    image_dir = args.dataset / "evaluation/images"
    label_dir = args.dataset / "evaluation/labels"

    if not args.model.is_file() or not image_dir.is_dir() or not label_dir.is_dir():
        parser.error("Model or frozen evaluation image/label directory is missing")

    images = sorted([*image_dir.glob("*.png"), *image_dir.glob("*.jpg"), *image_dir.glob("*.jpeg")])

    if not images:
        parser.error("No frozen evaluation images found")

    model = YOLO(args.model)
    counts = {name: defaultdict(int) for name in DATASET_CLASSES.values()}
    ignored_model_outputs = defaultdict(int)
    per_image: list[dict[str, object]] = []

    for image_path in images:
        label_path = label_dir / f"{image_path.stem}.txt"

        if not label_path.is_file():
            raise RuntimeError(f"Missing label: {label_path}")
        
        frame = cv2.imread(str(image_path))

        if frame is None:
            raise RuntimeError(f"Cannot read image: {image_path}")


        height, width = frame.shape[:2]
        truth = read_labels(label_path, width, height)

        result = model.predict(
            frame, 
            imgsz=512, 
            conf=args.confidence, 
            iou=args.nms_iou, 
            verbose=False
            )[0]
        
        predicted = []

        for box in result.boxes:
            model_class = int(box.cls[0])

            if model_class not in MODEL_TO_DATASET:
                ignored_model_outputs[str(model_class)] += 1
                continue

            predicted.append(Detection(
                class_id=MODEL_TO_DATASET[model_class],
                bbox_xyxy=tuple(float(value) for value in box.xyxy[0].tolist()),
                confidence=float(box.conf[0]),
            ))

        row = {"image": image_path.name}

        for class_id, name in DATASET_CLASSES.items():
            score = score_class(
                [item for item in predicted if item.class_id == class_id],
                [item for item in truth if item.class_id == class_id],
                args.match_iou,
            )

            for key in ("tp", "fp", "fn"):
                counts[name][key] += int(score[key])
                row[f"{name}_{key}"] = int(score[key])


        per_image.append(row)

    metrics = {name: summary(dict(class_counts)) for name, class_counts in counts.items()}

    report = {
        "dataset": "weapons-gun-knife-v1/frozen-evaluation",
        "evaluation_date": datetime.now(timezone.utc).isoformat(),
        "evaluation_image_count": len(images),
        "model": {"path": str(args.model.relative_to(AI_ROOT)).replace("\\", "/"), "sha256": sha256(args.model)},
        "model_class_map": {"0": "Gun", "1": "explosion", "2": "grenade", "3": "knife"},
        "dataset_class_map": {"0": "Gun", "1": "knife"},
        "confidence_threshold": args.confidence,
        "nms_iou_threshold": args.nms_iou,
        "match_iou_threshold": args.match_iou,
        "metrics": metrics,
        "ignored_explosion_grenade_predictions": dict(ignored_model_outputs),
        "limitations": [
            "Gun examples are source-separated by scene; knife source grouping is unknown.",
            "Twenty-five held-out WatchDog hard-negative frames come from one source clip.",
            "This is a fixed regression evaluation, not a field-performance estimate."
        ]
    }


    args.report_dir.mkdir(parents=True, exist_ok=True)

    (args.report_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    with (args.report_dir / "per_image_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_image[0]))
        writer.writeheader()
        writer.writerows(per_image)

    lines = ["# Weapon Detection Baseline v1", "", f"- Evaluation images: **{len(images)}**", f"- Current model: `{report['model']['path']}`", f"- Confidence / NMS / match IoU: **{args.confidence} / {args.nms_iou} / {args.match_iou}**", "", "| Class | TP | FP | FN | Precision | Recall | F1 |", "|---|---:|---:|---:|---:|---:|---:|"]

    for name, value in metrics.items():
        lines.append(f"| {name} | {value['tp']} | {value['fp']} | {value['fn']} | {value['precision']:.4f} | {value['recall']:.4f} | {value['f1']:.4f} |")

    lines += ["", "## Scope", "", "Only current-model Gun (class 0) and knife (class 3) outputs are scored. Explosion and grenade outputs have no matching ground truth in this two-class dataset and are not treated as Gun/knife false positives.", "", "## Limitations", *[f"- {item}" for item in report["limitations"]]]


    (args.report_dir / "baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


    print(json.dumps(metrics, indent=2))

    print(f"Weapon baseline report: {args.report_dir}")





if __name__ == "__main__":
    main()