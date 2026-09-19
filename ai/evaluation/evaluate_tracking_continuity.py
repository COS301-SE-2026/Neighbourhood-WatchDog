from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2

from pipeline.processing.cascaded_pipeline import CascadedPipeline, CascadedPipelineConfig

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("deep-sort-realtime is required to run this evaluator") from exc

try:
    from ultralytics import YOLO
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("ultralytics is required to run this evaluator") from exc


##an evaluation tool for testing whether deepsort keeps the same id for a person when they temporarily disappear


class EmptyWeaponModel:
    """
    The continuity evaluator only needs person detections.
    This prevents weapon inference from affecting the measurement.
    """

    def predict(self, *_args: Any, **kwargs: Any) -> list[Any]:
        return [] #always return empty, indicating no weapon detection (don't want weapon detection affecting the test)



##The function asks: Did the tracker recover the same ID after the person temporarily disappeared?
def summarize_track_ids(frame_track_ids: list[list[int]], max_gap_frames: int) -> dict[str, str]:
    """
    Summarise a single-target recorded clip.

    A frame with exactly one ID is considered an observed target frame.
    Empty frames represent a possible brief occlusion.

    A recovery means the same ID appears after a gap.
    A break means a different ID appears after a gap.
    """


    observed_frames = 0 #how mny frames contained one tracked person
    unique_ids: set[int] = set() #how many different deepsort ids appeared
    short_occlusion_recoveries = 0  #the same ids that come back after a short gap
    short_occlusion_breaks = 0 #a different id that appears after a short gap
    direct_id_switches = 0  #id switches without a gap

    previous_id: int | None = None #remember the last tracked id
    gap_frames = 0  #counting how many frames had no dtected target


    #processing each frame
    for ids in frame_track_ids:
        if len(ids) == 1:
            current_id = ids[0]
            observed_frames += 1
            unique_ids.add(current_id)


            #detecting direct id switches
            if previous_id is not None:
                if gap_frames == 0 and current_id != previous_id:
                    direct_id_switches +=1
                elif 0 < gap_frames <= max_gap_frames:
                    if current_id == previous_id:
                        short_occlusion_recoveries += 1
                    else:
                        short_occlusion_breaks += 1

            previous_id = current_id
            gap_frames = 0
            continue

        if previous_id is not None:
            gap_frames +=1

    return {
        "frames": len(frame_track_ids),
        "observed_frames": observed_frames,
        "unique_ids": len(unique_ids),
        "direct_id_switches": direct_id_switches,
        "short_occlusion_recoveries": short_occlusion_recoveries,
        "short_occlusion_breaks": short_occlusion_breaks

    }



#running a video through our pipeline
def evaluate_video(video_path: Path, person_model_path: Path, *, max_age: int, n_init: int, max_iou_distance: float) -> dict[str, Any]:

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    person_model = YOLO(str(person_model_path))

    tracker = DeepSort(
        max_age=max_age, #how long someone can survive without detection
        n_init=n_init,  ##how many detections are needed to confirm a track
        max_iou_distance=max_iou_distance,
        embedder="mobilenet",
        embedder_gpu=False,
        nms_max_overlap=0.5

    )

    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=EmptyWeaponModel(), #replaced the weapon model with this one cause we dont want it to intefer with this evaluation
        tracker=tracker,
        config=CascadedPipelineConfig(
            max_age=max_age,
            n_init=n_init,
            max_iou_distance=max_iou_distance

        )

    )

    frame_track_ids: list[list[int]] = []
    frames_read = 0

    #processign every video frame
    try:
        while True:
            ok, frame = capture.read()

            if not ok:
                break

            result = pipeline.process_frame(frame, timestamp=float(frames_read))

            ## extracting track ids
            ids = sorted(
                int(track["track_id"])
                for track in result.tracks
                if track.get("track_id") is not None
            )

            frame_track_ids.append(ids)
            frames_read += 1
    finally:
        capture.release()

    #summarize tracking
    summary = summarize_track_ids(frame_track_ids, max_gap_frames=max_age)

    return {
        "video": str(video_path),
        "configuration": {
            "max_age": max_age,
            "n_init": n_init,
            "max_iou_distance": max_iou_distance

        },
        **summary

    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure single-camera DeepSORT ID continuity.")

    parser.add_argument(
        "--video",
        required=True,
        type=Path,
        help="Path to a recorded single-camera video."

    )

    parser.add_argument(
        "--person-model",
        required=True,
        type=Path,
        help="Path to the YOLO person-detection model."

    )

    parser.add_argument(
        "--baseline-max-age",
        type=int,
        default=10

    )

    parser.add_argument(
        "--candidate-max-age",
        type=int,
        default=20

    )

    parser.add_argument(
        "--n-init",
        type=int,
        default=3

    )

    parser.add_argument(
        "--max-iou-distance",
        type=float,
        default=0.5

    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tracking-continuity-results.json")

    )


    args = parser.parse_args()

    baseline = evaluate_video(
        args.video,
        args.person_model,
        max_age=args.baseline_max_age,
        n_init=args.n_init,
        max_iou_distance=args.max_iou_distance

    )

    candidate = evaluate_video(
        args.video,
        args.person_model,
        max_age=args.candidate_max_age,
        n_init=args.n_init,
        max_iou_distance=args.max_iou_distance

    )

    result = {
        "baseline": baseline,
        "candidate": candidate,
        "comparison": {
            "recovery_delta": (candidate["short_occlusion_recoveries"] - baseline["short_occlusion_recoveries"]),
            "break_delta": (candidate["short_occlusion_breaks"] - baseline["short_occlusion_breaks"]),
            "unique_id_delta": (candidate["unique_ids"] - baseline["unique_ids"])
        }

    }

    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")


    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()