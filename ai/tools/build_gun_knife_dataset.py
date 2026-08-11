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

KNIFE_SPLITS = {
    "train": range(1, 70),
    "validation": range(70, 85),
    "evaluation": range(85, 115),
}


def parse_yolo(path: Path) -> list[tuple[int, float, float, float, float]]:
    """reads in yolo annotation file"""

    records = []

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

        records.append((class_id, *values))


    return records

def write_yolo(path: Path, records: list[tuple[int, float, float, float, float]]) -> None:
    """python annotations converted into yolo format"""

    path.write_text("".join(f"{class_id} {cx:.6f} {cy:.6f} {width:.6f} {height:.6f}\n" for class_id, cx, cy, width, height in records), encoding="utf-8")


def knife_split(image_name: str) -> str:
    """determines which split a knife image belongs to"""

    prefix = "Knife_scenario_"

    if not image_name.startswith(prefix) or not image_name.endswith(".png"):
        raise ValueError(f"Unexpected knife filename: {image_name}")

    number = int(image_name[len(prefix):-4])

    for split, numbers in KNIFE_SPLITS.items():
        if number in numbers:
            return split

    raise ValueError(f"Knife filename is outside the expected 1..114 range: {image_name}")

def prepare_output(output: Path, overwrite: bool) -> None:
    """output dataset directories"""

    if output.exists():
        if not overwrite:
            raise FileExistsError(f"Output already exists: {output}. Review it or pass --overwrite deliberately.")
        shutil.rmtree(output)

    for split in ("train", "validation", "evaluation"):
        (output / split / "images").mkdir(parents=True, exist_ok=True)
        (output / split / "labels").mkdir(parents=True, exist_ok=True)


def copy_item(image: Path, labels: list[tuple[int, float, float, float, float]],split: str, destination: Path, name:str) -> None:
    """copies one image and creates its corresponding label."""

    image_destination = destination / split / "images" / name
    label_destination = destination / split / "labels" / f"{Path(name).stem}.txt"
    shutil.copy2(image, image_destination)
    write_yolo(label_destination, labels)


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

    accepted = [row for row in audit_rows if row["decision"].strip().lower() == "keep"]
    unresolved = [row for row in audit_rows if row["decision"].strip().lower() not in {"keep", "exclude"}]

    if unresolved:
        parser.error(f"Audit has {len(unresolved)} unresolved row(s); decide keep or exclude before building.")

    if not accepted:
        parser.error("Audit has no accepted firearm examples.")

    scene_counts = Counter(row["scene_group"] for row in accepted)

    unknown_scenes = set(scene_counts) - set(GUN_SCENE_SPLITS)

    if unknown_scenes:
        parser.error(f"Unexpected scene group(s): {sorted(unknown_scenes)}")

    prepare_output(args.output, args.overwrite)

    ledger_rows: list[dict[str, str]] = []

    for row in accepted:
        source_image = AI_ROOT / row["source_image"]
        source_label = AI_ROOT / row["source_label"]
        split = GUN_SCENE_SPLITS[row["scene_group"]]

        labels = [(0, cx, cy, bw, bh) for class_id, cx, cy, bw, bh in parse_yolo(source_label) if class_id == 1]

        if not labels:
            raise RuntimeError(f"No generic-weapon box remains in accepted item: {source_label}")
        
        name = f"gun_{source_image.name}"

        copy_item(source_image, labels, split, args.output, name)

        ledger_rows.append({
            "dataset_item": name,
            "source_dataset": "cctv-weapon-dataset",
            "source_image": row["source_image"],
            "source_group": row["scene_group"],
            "split": split,
            "class_name": "Gun",
            "class_id": "0",
            "review_reason": row["reason"].strip() or "explicitly reviewed firearm"
        })

    knife_images = sorted((args.knife_source / "images").glob("*.png"), key=lambda item: int(item.stem.rsplit("_", 1)[1]))

    if len(knife_images) != 114:
        parser.error(f"Expected 114 knife images, found {len(knife_images)}")

    for source_image in knife_images:
        source_label = args.knife_source / "labels" / f"{source_image.stem}.txt"

        if not source_label.is_file():
            raise RuntimeError(f"Missing knife label: {source_label}")
        
        split = knife_split(source_image.name)
        labels = [(1, cx, cy, bw, bh) for class_id, cx, cy, bw, bh in parse_yolo(source_label) if class_id == 1]

        if not labels:
            raise RuntimeError(f"No knife box in source item: {source_label}")
        
        name = f"knife_{source_image.name}"

        copy_item(source_image, labels, split, args.output, name)

        ledger_rows.append({
            "dataset_item": name,
            "source_dataset": "cctv-knife-detection-dataset",
            "source_image": str(source_image.relative_to(AI_ROOT)).replace("\\", "/"),
            "source_group": "unknown-source-grouping; contiguous filename block",
            "split": split,
            "class_name": "knife",
            "class_id": "1",
            "review_reason": "source label retained; quality audit still required before final training"
        })

    with (args.output / "source_ledger.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["dataset_item", "source_dataset", "source_image", "source_group", "split", "class_name", "class_id", "review_reason"]

        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ledger_rows)

    (args.output / "dataset.yaml").write_text(
        "path: .\n"
        "train: train/images\n"
        "val: validation/images\n"
        "test: evaluation/images\n\n"
        "names:\n"
        "  0: Gun\n"
        "  1: knife\n",
        encoding="utf-8"
    )

    summary = Counter((row["split"], row["class_name"]) for row in ledger_rows)

    print(f"Built reviewed Gun/knife dataset: {args.output}")

    for split in ("train", "validation", "evaluation"):
        print(f"{split}: Gun={summary[(split, 'Gun')]}, knife={summary[(split, 'knife')]}")
        
    print("IMPORTANT: add 100+ real WatchDog hard-negative images (empty label files) before training.")
    print("IMPORTANT: knife source grouping is unknown; document this split limitation in final evaluation.")


if __name__ == "__main__":
    main()