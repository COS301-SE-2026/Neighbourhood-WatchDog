"""
copies those approved frames into the curated dataset and writes an empty YOLO label file for each one

Run from ai/:
    python tools/integrate_hard_negatives.py
"""

from __future__ import annotations
from collections import Counter
from pathlib import Path
import argparse
import csv
import shutil


AI_ROOT = Path(__file__).resolve().parents[1]
AUDIT_ROOT = AI_ROOT / "data/curated/weapons-gun-knife-v1/audit/hard-negative-candidates"
DEFAULT_LEDGER = AUDIT_ROOT / "hard_negative_review.csv"
DEFAULT_DATASET = AI_ROOT / "data/curated/weapons-gun-knife-v1/dataset"


def main() -> None:

    parser = argparse.ArgumentParser(description="Integrate manually approved WatchDog weapon-negative frames.")

    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--overwrite", action="store_true", help="Replace an already integrated hard-negative image/label with the same name.")
    args = parser.parse_args()

    if not args.ledger.is_file():
        parser.error(f"Review ledger not found: {args.ledger}")

    if not (args.dataset / "dataset.yaml").is_file():
        parser.error(f"Curated dataset is incomplete or missing: {args.dataset}")


    with args.ledger.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    required = {"candidate_id", "source_file", "frame_number", "timestamp_seconds", "assigned_split", "candidate_path", "decision", "reason"}

    if not rows or set(rows[0]) != required:
        parser.error("Unexpected review-ledger columns; do not integrate an unrecognised ledger.")

    unresolved = [
        row["candidate_id"]
        for row in rows
        if row["decision"].strip().lower() not in {"keep", "exclude"}
    ]

    if unresolved:
        parser.error(f"{len(unresolved)} review row(s) are unresolved; review every candidate first.")

    approved = [row for row in rows if row["decision"].strip().lower() == "keep"]

    if not approved:
        parser.error("No candidates are approved; nothing will be copied.")

    counts: Counter[str] = Counter()
    audit_rows: list[dict[str, str]] = []

    for row in approved:
        split = row["assigned_split"].strip()

        if split not in {"train", "validation", "evaluation"}:
            parser.error(f"Invalid split for {row['candidate_id']}: {split!r}")

        source = AUDIT_ROOT / row["candidate_path"]

        if not source.is_file():
            parser.error(f"Candidate image missing: {source}")

        image_name = f"watchdog_{source.name}"
        image_target = args.dataset / split / "images" / image_name
        label_target = args.dataset / split / "labels" / f"{Path(image_name).stem}.txt"

        if (image_target.exists() or label_target.exists()) and not args.overwrite:
            parser.error(f"Target already exists for {row['candidate_id']}: {image_target}. " "Review it or rerun with --overwrite deliberately.")

        image_target.parent.mkdir(parents=True, exist_ok=True)
        label_target.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, image_target)

        label_target.write_text("", encoding="utf-8")

        counts[split] += 1

        audit_rows.append({
            "dataset_item": image_name,
            "source_file": row["source_file"],
            "frame_number": row["frame_number"],
            "timestamp_seconds": row["timestamp_seconds"],
            "split": split,
            "decision": "keep",
            "review_reason": row["reason"].strip() or "confirmed no Gun or knife",
            "label_policy": "empty YOLO label: confirmed weapon-negative"
        })

    output_ledger = args.dataset / "watchdog_hard_negative_ledger.csv"

    with output_ledger.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(audit_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)

    print(f"Integrated {len(approved)} approved WatchDog hard negatives into {args.dataset}")


    for split in ("train", "validation", "evaluation"):
        print(f"{split}: {counts[split]} copied with empty labels")

    print(f"Audit ledger: {output_ledger}")




if __name__ == "__main__":
    main()