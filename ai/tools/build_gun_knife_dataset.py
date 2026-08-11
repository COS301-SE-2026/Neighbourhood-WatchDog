"""
Final YOLO dataset for detecting two classes: Gun and knife
"""

from __future__ import annotations
from collections import Counter
from pathlib import Path
import argparse
import csv
import shutil


AI_ROOT = Path(__file__).resolve().parents[1]
AUDIT_CSV = AI_ROOT / "data/curated/weapons-gun-knife-v1/audit/gun_review.csv"
WEAPON_SOURCE = AI_ROOT / "data/external/cctv-weapon-dataset/Dataset"
KNIFE_SOURCE = AI_ROOT / "data/external/cctv-knife-detection-dataset/Knife_Dataset"
DEFAULT_OUTPUT = AI_ROOT / "data/curated/weapons-gun-knife-v1/dataset"

GUN_SCENE_SPLITS = {
    "Scene1": "train",
    "Scene2": "evaluation",
    "Scene3": "train",
    "Scene4": "train",
    "Scene5": "train",
    "Scene6": "validation",
}


def knife_split(number: int) -> str:

    if not 1 <= number <= 114:
        raise ValueError(f"Knife filename number must be 1..114, got {number}")
    if number <= 69:
        return "train"
    if number <= 83:
        return "validation"
    return "evaluation"


def parse_yolo(path: Path) -> list[tuple[int, float, float, float, float]]:

    records: list[tuple[int, float, float, float, float]] = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue

        fields = line.split()

        if len(fields) != 5:
            raise ValueError(f"{path}:{line_number}: expected 5 YOLO fields")
        
        class_id = int(fields[0])

        cx, cy, width, height = (float(value) for value in fields[1:])

        if not all(0.0 <= value <= 1.0 for value in (cx, cy, width, height)):
            raise ValueError(f"{path}:{line_number}: normalized coordinates must be in [0, 1]")
        
        records.append((class_id, cx, cy, width, height))


    return records


def write_yolo(path: Path, records: list[tuple[int, float, float, float, float]]) -> None:

    path.write_text(
        "".join(
            f"{class_id} {cx:.6f} {cy:.6f} {width:.6f} {height:.6f}\n"
            for class_id, cx, cy, width, height in records
        ),
        encoding="utf-8",
    )


def prepare_output(output: Path, overwrite: bool) -> None:

    if output.exists():
        if not overwrite:
            raise FileExistsError(f"Output already exists: {output}. Review it or pass --overwrite deliberately.")
        shutil.rmtree(output)

    for split in ("train", "validation", "evaluation"):
        (output / split / "images").mkdir(parents=True, exist_ok=True)
        (output / split / "labels").mkdir(parents=True, exist_ok=True)


def copy_item(image: Path, labels: list[tuple[int, float, float, float, float]], split: str, destination: Path, filename: str,) -> None:

    shutil.copy2(image, destination / split / "images" / filename)
    write_yolo(destination / split / "labels" / f"{Path(filename).stem}.txt", labels)


def knife_number(image: Path) -> int:

    prefix = "Knife_scenario_"

    if image.suffix.lower() != ".png" or not image.stem.startswith(prefix):
        raise ValueError(f"Unexpected knife filename: {image.name}")

    
    return int(image.stem.removeprefix(prefix))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the reviewed Gun/knife YOLO dataset.")

    parser.add_argument("--audit-csv", type=Path, default=AUDIT_CSV)
    parser.add_argument("--weapon-source", type=Path, default=WEAPON_SOURCE)
    parser.add_argument("--knife-source", type=Path, default=KNIFE_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if not args.audit_csv.is_file():
        parser.error(f"Audit CSV not found: {args.audit_csv}")

    with args.audit_csv.open(newline="", encoding="utf-8") as handle:
        audit_rows = list(csv.DictReader(handle))

    unresolved = [r for r in audit_rows if r["decision"].strip().lower() not in {"keep", "exclude"}]
    accepted = [r for r in audit_rows if r["decision"].strip().lower() == "keep"]

    if unresolved:
        parser.error(f"Audit has {len(unresolved)} unresolved row(s).")

    if not accepted:
        parser.error("Audit has no accepted firearm examples.")

    unknown_scenes = {r["scene_group"] for r in accepted} - set(GUN_SCENE_SPLITS)

    if unknown_scenes:
        parser.error(f"Unexpected scene groups: {sorted(unknown_scenes)}")

    knife_images = sorted(
        (args.knife_source / "images").glob("*.png"), key=knife_number
    )


    if len(knife_images) != 114:
        parser.error(f"Expected 114 knife images, found {len(knife_images)}")

    prepare_output(args.output, args.overwrite)
    ledger_rows: list[dict[str, str]] = []

    for row in accepted:
        image = AI_ROOT / row["source_image"]
        label = AI_ROOT / row["source_label"]
        split = GUN_SCENE_SPLITS[row["scene_group"]]


        gun_labels = [(0, cx, cy, width, height) for class_id, cx, cy, width, height in parse_yolo(label) if class_id == 1]

        if not gun_labels:
            raise RuntimeError(f"No generic weapon box remains in accepted item: {label}")
        
        filename = f"gun_{image.name}"

        copy_item(image, gun_labels, split, args.output, filename)


        ledger_rows.append({
            "dataset_item": filename, "source_dataset": "cctv-weapon-dataset",
            "source_image": row["source_image"], "source_group": row["scene_group"],
            "split": split, "content_type": "Gun", "class_id": "0",
            "review_reason": row["reason"].strip() or "explicitly reviewed firearm"
        })

    for image in knife_images:
        number = knife_number(image)

        label = args.knife_source / "labels" / f"{image.stem}.txt"

        if not label.is_file():
            raise RuntimeError(f"Missing knife label: {label}")
        
        split = knife_split(number)

        knife_labels = [(1, cx, cy, width, height) for class_id, cx, cy, width, height in parse_yolo(label) if class_id == 1]
        content_type = "knife" if knife_labels else "background_no_knife"
        filename = f"knife_{image.name}"
        
        copy_item(image, knife_labels, split, args.output, filename)

        ledger_rows.append({
            "dataset_item": filename, "source_dataset": "cctv-knife-detection-dataset",
            "source_image": str(image.relative_to(AI_ROOT)).replace("\\", "/"),
            "source_group": "unknown-source-grouping; contiguous filename block",
            "split": split, "content_type": content_type,
            "class_id": "1" if knife_labels else "",
            "review_reason": "source knife label retained" if knife_labels else "source label contains person only; retained as empty-label background"
        })

    fields = ["dataset_item", "source_dataset", "source_image", "source_group", "split", "content_type", "class_id", "review_reason"]

    with (args.output / "source_ledger.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)

        writer.writeheader()
        writer.writerows(ledger_rows)

    (args.output / "dataset.yaml").write_text(
        "path: .\ntrain: train/images\nval: validation/images\ntest: evaluation/images\n\n"
        "names:\n  0: Gun\n  1: knife\n",
        encoding="utf-8"
    )

    summary = Counter((r["split"], r["content_type"]) for r in ledger_rows)

    print(f"Built reviewed Gun/knife dataset: {args.output}")

    for split in ("train", "validation", "evaluation"):
        print(
            f"{split}: Gun={summary[(split, 'Gun')]}, "
            f"knife-positive={summary[(split, 'knife')]}, "
            f"background={summary[(split, 'background_no_knife')]}"
        )

    print("IMPORTANT: add 100+ real WatchDog hard-negative images (empty labels) before training.")
    
    print("IMPORTANT: knife source grouping is unknown; document this split limitation in the final report.")


if __name__ == "__main__":
    main()