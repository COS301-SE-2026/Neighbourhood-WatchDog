"""
create a review-only, source-separated set of WatchDog hard-negative candidates.

Run from ai/:
    python tools/prepare_hard_negative_audit.py
"""

from __future__ import annotations
from pathlib import Path

import argparse
import csv
import html
import shutil
import cv2


AI_ROOT = Path(__file__).resolve().parents[1]
FOOTAGE_DIR = AI_ROOT / "tests" / "footage"
DEFAULT_OUTPUT = AI_ROOT / "data" / "curated" / "weapons-gun-knife-v1" / "audit" / "hard-negative-candidates"
SAMPLES_PER_VIDEO = 25


SOURCES = (
    ("clear-presence.mp4", "train"),
    ("blurred-presence.mp4", "train"),
    ("blurred-no_presence.mp4", "validation"),
    ("clear-no_presence.mp4", "evaluation"),
)


def selected_indices(frame_count: int, sample_count: int) -> list[int]:
    """return deterministic, evenly-spaced indices that never exceed frame_count - 1."""

    if frame_count < sample_count:
        raise RuntimeError(f"Video has only {frame_count} readable frames; need {sample_count} candidates.")

    
    return [round(index * (frame_count - 1) / (sample_count - 1)) for index in range(sample_count)]


def decode_selected_frames(video_path: Path, sample_count: int) -> tuple[float, list[tuple[int, object]]]:
    """decode sequentially because opencv seeking can be unreliable with mp4 files."""

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    reported_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    fps = float(capture.get(cv2.CAP_PROP_FPS))

    if reported_count <= 0 or fps <= 0:
        capture.release()
        raise RuntimeError(f"Invalid video metadata: {video_path}")

    wanted = set(selected_indices(reported_count, sample_count))
    extracted: list[tuple[int, object]] = []
    frame_number = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_number in wanted:
            extracted.append((frame_number, frame))
        frame_number += 1

    capture.release()

    if len(extracted) != sample_count:
        raise RuntimeError(f"Only extracted {len(extracted)}/{sample_count} selected frames from {video_path}. ""Check the clip or adjust the extractor.")


    return fps, extracted


def write_index(rows: list[dict[str, str]], output: Path) -> None:

    cards = []

    for row in rows:
        image = html.escape(row["candidate_path"])
        identifier = html.escape(row["candidate_id"])
        source = html.escape(row["source_file"])
        split = html.escape(row["assigned_split"])

        cards.append(
            f"<article><img src='{image}' loading='lazy' alt='{identifier}'>"
            f"<h3>{identifier}</h3><p>{source}<br>split: <strong>{split}</strong><br>"
            f"frame {row['frame_number']} at {row['timestamp_seconds']}s</p></article>"
        )

    page = """
    <!doctype html>
        <html lang=\"en\"><head><meta charset=\"utf-8\"><title>WatchDog hard-negative review</title>
        <style>body{font-family:system-ui;margin:24px;background:#f7f7f8;color:#222}h1{margin-bottom:4px}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}article{background:#fff;border:1px solid #ddd;padding:10px;border-radius:8px}img{width:100%;height:190px;object-fit:contain;background:#111}h3{font-size:14px;margin:8px 0 4px}p{font-size:13px;margin:0;line-height:1.45}</style>
        </head><body><h1>Hard-negative candidate review</h1>
        <p>Review every image. Mark the CSV decision <code>keep</code> only when no Gun and no knife is visible; otherwise use <code>exclude</code> and state why. These candidates are not yet part of the dataset.</p>
        <div class=\"grid\">__CARDS__</div></body></html>
    """
    (output / "index.html").write_text(page.replace("__CARDS__", "\n".join(cards)), encoding="utf-8")


def main() -> None:

    parser = argparse.ArgumentParser(description="Extract review-only WatchDog hard-negative candidates.")

    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true", help="Replace the candidate audit folder deliberately.")
    args = parser.parse_args()

    if args.output.exists():
        if not args.overwrite:
            raise FileExistsError(f"Output already exists: {args.output}. Review it or pass --overwrite deliberately.")
        
        shutil.rmtree(args.output)

    rows: list[dict[str, str]] = []

    for filename, split in SOURCES:
        video_path = FOOTAGE_DIR / filename
        if not video_path.is_file():
            raise FileNotFoundError(f"Required WatchDog fixture not found: {video_path}")

        fps, frames = decode_selected_frames(video_path, SAMPLES_PER_VIDEO)
        target_dir = args.output / split / "images"
        target_dir.mkdir(parents=True, exist_ok=True)
        stem = video_path.stem

        for frame_number, frame in frames:
            candidate_id = f"negative_{stem}_f{frame_number:06d}"
            image_path = target_dir / f"{candidate_id}.jpg"

            if not cv2.imwrite(str(image_path), frame):
                raise RuntimeError(f"Could not write candidate image: {image_path}")
            
            rows.append({
                "candidate_id": candidate_id,
                "source_file": str(video_path.relative_to(AI_ROOT)).replace("\\", "/"),
                "frame_number": str(frame_number),
                "timestamp_seconds": f"{frame_number / fps:.6f}",
                "assigned_split": split,
                "candidate_path": str(image_path.relative_to(args.output)).replace("\\", "/"),
                "decision": "",
                "reason": ""
            })

    ledger_path = args.output / "hard_negative_review.csv"
    fieldnames = ["candidate_id", "source_file", "frame_number", "timestamp_seconds", "assigned_split", "candidate_path", "decision", "reason"]


    with ledger_path.open("w", newline="", encoding="utf-8") as handle:

        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    write_index(rows, args.output)
    
    print(f"Created {len(rows)} review-only candidates in {args.output}")
    print(f"Review ledger: {ledger_path}")
    print(f"Preview page: {args.output / 'index.html'}")
    print("Do not copy these frames into dataset/ until each ledger row is marked keep or exclude.")


if __name__ == "__main__":
    main()