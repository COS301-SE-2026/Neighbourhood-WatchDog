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