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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def yolo_to_xyxy(values: list[float], width: int, height: int) -> tuple[float, float, float, float]:
    _, x_center, y_center, box_width, box_height = values
    x_center, box_width = x_center * width, box_width * width
    y_center, box_height = y_center * height, box_height * height

    return (
        x_center - box_width / 2,
        y_center - box_height / 2,
        x_center + box_width / 2,
        y_center + box_height / 2,
    )


def read_ground_truth(label_path: Path, width: int, height: int) -> list[Detection]:
    """Read a YOLO label file. An existing empty file is an intentional negative."""

    if not label_path.exists():
        raise FileNotFoundError(
            f"Missing human ground-truth label: {label_path}. Create an empty file for a confirmed negative frame."
        )
    
    detections: list[Detection] = []

    for line_number, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue

        parts = raw_line.split()

        if len(parts) != 5:
            raise ValueError(f"{label_path}:{line_number}: expected 5 YOLO values, got {len(parts)}")
        
        values = [float(value) for value in parts]

        class_id = int(values[0])

        if class_id not in CLASS_NAMES:
            raise ValueError(f"{label_path}:{line_number}: unknown class ID {class_id}")

        if not all(0.0 <= value <= 1.0 for value in values[1:]):
            raise ValueError(f"{label_path}:{line_number}: YOLO coordinates must be between 0 and 1")

        detections.append(Detection(class_id=class_id, bbox_xyxy=yolo_to_xyxy(values, width, height)))

    return detections


def predict(frame, person_model: YOLO, threat_model: YOLO, person_confidence: float, weapon_confidence: float) -> list[Detection]:

    predictions: list[Detection] = []

    person_results = person_model.predict(
        frame, 
        imgsz=640, 
        conf=person_confidence, 
        classes=[0], 
        verbose=False
    )

    for box in person_results[0].boxes:
        predictions.append(Detection(
            class_id=0,
            bbox_xyxy=tuple(float(value) for value in box.xyxy[0].tolist()),
            confidence=float(box.conf[0]),
        ))

    threat_results = threat_model.predict(frame, 
                                          imgsz=512, 
                                          conf=weapon_confidence, 
                                          verbose=False
                                          )
    
    for box in threat_results[0].boxes:
        threat_class_id = int(box.cls[0])

        if threat_class_id not in THREAT_MODEL_TO_EVALUATION_CLASS:
            raise ValueError(f"Unexpected best.pt class ID {threat_class_id}; update the evaluation mapping.")

        predictions.append(Detection(
            class_id=THREAT_MODEL_TO_EVALUATION_CLASS[threat_class_id],
            bbox_xyxy=tuple(float(value) for value in box.xyxy[0].tolist()),
            confidence=float(box.conf[0]),
        ))

    return predictions


def only_class(detections: list[Detection], class_id: int) -> list[Detection]:

    return [item for item in detections if item.class_id == class_id]


def weapon_view(detections: list[Detection]) -> list[Detection]:
    """Collapse all valid weapon classes into one class for the combined metric."""

    return [Detection(99, item.bbox_xyxy, item.confidence) for item in detections if item.class_id in WEAPON_CLASS_IDS]


def add_counts(target: dict[str, int], score: dict[str, object]) -> None:

    target["tp"] += int(score["tp"])
    target["fp"] += int(score["fp"])
    target["fn"] += int(score["fn"])


def calculate_summary(counts: dict[str, int]) -> dict[str, float | int | str]:

    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
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


def write_markdown_report(report_path: Path, result: dict[str, object]) -> None:

    lines = [
        "# WatchDog Detection Baseline v1",
        "",
        f"- **Run date:** {result['evaluation_date']}",
        f"- **Evaluation frames/images:** {result['evaluation_item_count']}",
        f"- **IoU match threshold:** {result['iou_match_threshold']}",
        f"- **Person model:** `{result['person_model']['path']}` (confidence `{result['person_model']['confidence_threshold']}`)",
        f"- **Threat model:** `{result['threat_model']['path']}` (confidence `{result['threat_model']['confidence_threshold']}`)",
        "",
        "## Metrics",
        "",
        "| Class | TP | FP | FN | Precision | Recall | F1 | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for name, metric in result["classes"].items():
        lines.append(
            f"| {name} | {metric['tp']} | {metric['fp']} | {metric['fn']} | "
            f"{metric['precision']:.4f} | {metric['recall']:.4f} | {metric['f1']:.4f} | {metric['status']} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "This is an offline, fixed-dataset raw-detection baseline. It excludes DeepSort, zones, alert cooldowns, API calls and alert creation.",
        "A class with no human-labelled positive objects is marked **not measurable** for recall/F1; do not treat a zero value as a model result.",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:

    parser = argparse.ArgumentParser(description="Evaluate WatchDog detection accuracy against human YOLO labels.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--labels-dir", type=Path, default=LABELS_DIR)
    parser.add_argument("--report-dir", type=Path, default=EVALUATION_DIR / "reports" / "baseline-v1")
    parser.add_argument("--person-conf", type=float, default=0.25)
    parser.add_argument("--weapon-conf", type=float, required=True)
    parser.add_argument("--match-iou", type=float, default=0.50)
    args = parser.parse_args()

    if not 0 < args.person_conf <= 1 or not 0 < args.weapon_conf <= 1 or not 0 < args.match_iou <= 1:
        parser.error("confidence and IoU values must be greater than 0 and no more than 1")

    if not args.manifest.exists():
        parser.error(f"Manifest does not exist: {args.manifest}. Run extract_eval_frames.py first.")

    with args.manifest.open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))

    if not manifest:
        parser.error("Manifest contains no evaluation items")

    person_model = YOLO(PERSON_MODEL_PATH)
    threat_model = YOLO(THREAT_MODEL_PATH)
    all_counts = {name: {"tp": 0, "fp": 0, "fn": 0} for name in (*CLASS_NAMES.values(), "weapon")}

    for row in manifest:
        frame_path = AI_ROOT / row["frame_path"]
        frame = cv2.imread(str(frame_path))
        if frame is None:
            raise RuntimeError(f"Cannot read manifest frame: {frame_path}")

        height, width = frame.shape[:2]
        ground_truth = read_ground_truth(args.labels_dir / f"{row['frame_id']}.txt", width, height)
        predictions = predict(frame, person_model, threat_model, args.person_conf, args.weapon_conf)

        for class_id, class_name in CLASS_NAMES.items():
            score = score_class(only_class(predictions, class_id), only_class(ground_truth, class_id), args.match_iou)
            add_counts(all_counts[class_name], score)

        combined = score_class(weapon_view(predictions), weapon_view(ground_truth), args.match_iou)

        add_counts(all_counts["weapon"], combined)

    args.report_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "dataset": "watchdog-real-footage-baseline-v1",
        "evaluation_date": datetime.now(timezone.utc).isoformat(),
        "evaluation_item_count": len(manifest),
        "manifest": str(args.manifest.relative_to(AI_ROOT)).replace("\\", "/"),
        "iou_match_threshold": args.match_iou,
        "person_model": {
            "path": str(PERSON_MODEL_PATH.relative_to(AI_ROOT)).replace("\\", "/"),
            "sha256": sha256(PERSON_MODEL_PATH),
            "confidence_threshold": args.person_conf,
            "imgsz": 640
        },
        "threat_model": {
            "path": str(THREAT_MODEL_PATH.relative_to(AI_ROOT)).replace("\\", "/"),
            "sha256": sha256(THREAT_MODEL_PATH),
            "confidence_threshold": args.weapon_conf,
            "imgsz": 512
        },
        "classes": {name: calculate_summary(counts) for name, counts in all_counts.items()},
    }

    (args.report_dir / "metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    with (args.report_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("class", "tp", "fp", "fn", "ground_truth_count", "prediction_count", "precision", "recall", "f1", "status"))
        writer.writeheader()
        for name, metric in result["classes"].items():
            writer.writerow({"class": name, **metric})

    write_markdown_report(args.report_dir / "baseline.md", result)

    print(f"Baseline report written to {args.report_dir}")


if __name__ == "__main__":
    main()