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


def write_html(rows: list[dict[str, str]], audit_dir: Path) -> None:
    """generates an html webpage for reviewing the images."""

    lines = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Gun curation audit</title>",
        "<style>body{font-family:system-ui;margin:24px;background:#f7f7f7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}.card{background:white;padding:12px;border-radius:8px;box-shadow:0 1px 3px #bbb}.card img{width:100%;height:auto}.meta{font-size:14px;margin-top:8px}</style>",
        "</head><body><h1>Gun curation audit</h1>",
        "<p>Every red box is only a generic <code>weapon</code> label. Mark <code>keep</code> in <code>gun_review.csv</code> only if it is clearly a firearm. Do not use this page as ground truth.</p>",
        "<div class='grid'>",
    ]

    for row in rows:
        image_name = Path(row["source_image"]).name

        preview = f"previews/{image_name}"

        lines += [
            "<div class='card'>",
            f"<a href='{preview}'><img src='{preview}' alt='{image_name}'></a>",
            f"<div class='meta'><strong>{image_name}</strong><br>Scene: {row['scene_group']} · generic weapon boxes: {row['weapon_box_count']}<br>Decision: review in <code>gun_review.csv</code></div>",
            "</div>",
        ]

    lines += ["</div></body></html>"]

    (audit_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:

    parser = argparse.ArgumentParser(description="Create a manual firearm-curation audit pack.")


    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing review CSV.")

    args = parser.parse_args()

    images_dir = args.source_dir / "images"
    labels_dir = args.source_dir / "labels"
    
    if not images_dir.is_dir() or not labels_dir.is_dir():
        parser.error("source-dir must contain images/ and labels/")


    args.audit_dir.mkdir(parents=True, exist_ok=True)
    previews_dir = args.audit_dir / "previews"
    previews_dir.mkdir(exist_ok=True)
    review_csv = args.audit_dir / "gun_review.csv"

    if review_csv.exists() and not args.overwrite:
        parser.error(f"Review file already exists: {review_csv}. Preserve completed decisions, or pass --overwrite deliberately.")

    rows: list[dict[str, str]] = []

    for image_path in sorted(images_dir.glob("*.png")):
        label_path = labels_dir / f"{image_path.stem}.txt"

        if not label_path.exists():
            raise RuntimeError(f"Missing label file: {label_path}")
        
        weapon_count = sum(class_id == 1 for class_id, *_ in parse_yolo(label_path))

        if weapon_count == 0:
            continue

        row = {
            "source_image": str(image_path.relative_to(AI_ROOT)).replace("\\", "/"),
            "source_label": str(label_path.relative_to(AI_ROOT)).replace("\\", "/"),
            "scene_group": scene_group(image_path.name),
            "weapon_box_count": str(weapon_count),
            "decision": "",
            "reason": "",
            "assigned_split": "",
        }

        rows.append(row)

        draw_preview(image_path, label_path, previews_dir / image_path.name)

    with review_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


    write_html(rows, args.audit_dir)
    
    print(f"Created {len(rows)} firearm-review rows: {review_csv}")
    print(f"Open this review page in a browser: {args.audit_dir / 'index.html'}")
    print("For each row, set decision to keep or exclude, add a reason, and assign train/validation/evaluation only after source-level split decisions are made.")


if __name__ == "__main__":
    main()