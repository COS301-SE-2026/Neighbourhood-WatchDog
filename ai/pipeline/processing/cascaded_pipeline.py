"""
1) Human detection on the full frame
2) Threat detection only after each human crop
3) DEEPSORT tracking of person detections
4) Zone based behaviour classification using in-memory track history


"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Sequence

import time


try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except ImportError: # pragma: no cover
    DeepSort = None # type: ignore[assignment]



PERSON_CLASS_ID = 0
DETECTION_HUMAN = "HUMAN_PRESENCE"
DETECTION_LOITERING = "LOITERING"
DETECTION_PERIMETER_SCAN = "PERIMETER_SCAN"
DETECTION_WEAPON = "WEAPON_DETECTED"

SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class CascadedPipelineConfig:

    person_confidence: float = 0.25
    person_iou: float = 0.70
    person_imgsz: int = 640
    weapon_confidence: float = 0.50
    weapon_iou: float = 0.50
    weapon_imgsz: int = 512
    max_age: int = 10
    n_init: int = 3
    max_iou_distance: float = 0.5
    loitering_threshold_seconds: float = 30.0
    scan_time_window_seconds: float = 30.0
    scan_crossing_threshold: int = 3
    history_retention_seconds: float = 300.0


@dataclass
class PipelineResult:
    tracks: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)



@dataclass
class _TrackHistory:

    last_seen: float = 0.0
    previous_inside: tuple[bool, ...] | None = None
    entered_at: dict[int, float] = field(default_factory=dict)
    crossings: dict[int, deque[float]] = field(default_factory=dict)
    last_emitted_type: str | None = None


class CascadedPipeline:
    """running the local stages for one camera"""

    def __init__(self, *, person_model: Any, weapon_model: Any, 
                 zones: Sequence[Sequence[Sequence[float]]] = (), 
                 zone_ids: Sequence[str] = (), config: CascadedPipelineConfig | None = None, 
                 tracker: Any | None = None, inference_lock: Lock | None = None) -> None:
        
        self.person_model = person_model
        self.weapon_model = weapon_model
        self.zones = tuple(tuple(tuple(point) for point in polygon) for polygon in zones)
        self.zone_ids = tuple(str(value) for value in zone_ids)
        self.config = config or CascadedPipelineConfig()
        self.inference_lock = inference_lock

        if tracker is not None:
            self.tracker = tracker
        else:
            if DeepSort is None:
                raise RuntimeError("deep-sort-realtime is required unless a tracker is injected")

            self.tracker = DeepSort(
                max_age=self.config.max_age, 
                n_init=self.config.n_init, 
                max_iou_distance=self.config.max_iou_distance,
                embedder="mobilenet",
                embedder_gpu=False,
                nms_max_overlap=0.5,
            )

        self._histories: dict[int, _TrackHistory] = {}

    
    def process_frame(self, frame: Any, *, timestamp: float | None = None) -> PipelineResult:
        """"process one BGR frame and returns the current annotations plus new events.

        ``events`` is edge-triggered: a track generates one event when its classification first becomes active, and another only when its classification changes.  This prevents one backend alert per frame.
        """
        now = time.monotonic() if timestamp is None else float(timestamp)

        persons = self._detect_persons(frame)

        if not persons:
            self._cleanup_histories(now)
            return PipelineResult()

        enriched_persons = self._enrich_with_weapons(frame, persons)
        confirmed_tracks = self._track(frame, enriched_persons)

        tracks: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []

        for track in confirmed_tracks:
            track_id = int(track["track_id"])
            behaviour = self._classify_behaviour(track, now, frame.shape[:2])

            output = {
                **track,
                **behaviour,
                "is_confirmed": True

            } #dictionary containing everything from track, behaviour, and appending a 'true confirmation'


            tracks.append(output)

            history = self._histories[track_id]


            if history.last_emitted_type != output["detection_type"]:
                events.append(dict(output))

                history.last_emitted_type = output["detection_type"]

        self._cleanup_histories(now)



        return PipelineResult(tracks=tracks, events=events)


    def _detect_persons(self, frame: Any) -> list[dict[str, Any]]:

        with self._inference_guard():

            results = self.person_model.predict(
                frame,
                verbose=False,
                conf=self.config.person_confidence,
                iou=self.config.person_iou,
                imgsz=self.config.person_imgsz,
                classes=[PERSON_CLASS_ID]

            )

        persons: list[dict[str, Any]] = []

        for box in self._boxes_from_result(results):

            class_id = int(self._scalar(box.cls[0]))
            confidence = float(self._scalar(box.conf[0]))

            if class_id != PERSON_CLASS_ID or confidence < self.config.person_confidence:
                continue

            bbox = self._xyxy(box)
            if self._valid_bbox(bbox):
                persons.append({
                    "bbox": bbox,
                    "confidence": confidence,
                    "crop": self._crop(frame, bbox),

                    "weapon_detected": False,
                    "weapon_type": None,
                    "weapon_confidence": None

                })

                
        return persons

    def _enrich_with_weapons(self, frame: Any, persons: list[dict[str, Any]]) -> list[dict[str, Any]]:

        enriched: list[dict[str, Any]] = []

        for person in persons:
            x1, y1, x2, y2 = [int(value) for value in person["bbox"]]

            crop = person["crop"]

            if crop is None or crop.size == 0:
                enriched.append(person)
                continue

            with self._inference_guard():

                results = self.weapon_model.predict(
                    crop,
                    verbose=False,
                    conf=self.config.weapon_confidence,
                    iou=self.config.weapon_iou,
                    imgsz=self.config.weapon_imgsz

                )

            best_weapon: tuple[float, str, list[float]] | None = None

            
            for box in self._boxes_from_result(results):
                confidence = float(self._scalar(box.conf[0]))


                if confidence < self.config.weapon_confidence:
                    continue

                local_bbox = self._xyxy(box)
                absolute_bbox = [
                    local_bbox[0] + x1,
                    local_bbox[1] + y1,
                    local_bbox[2] + x1,
                    local_bbox[3] + y1
                ]

                class_id = int(self._scalar(box.cls[0]))
                label = self._class_name(self.weapon_model, class_id)

                if best_weapon is None or confidence > best_weapon[0]:
                    best_weapon = (confidence, label, absolute_bbox)

            item = dict(person)

            if best_weapon is not None:
                confidence, label, _ = best_weapon
                item.update({
                    "weapon_detected": True,
                    "weapon_type": label,
                    "weapon_confidence": confidence


                })


            enriched.append(item)

        return enriched

    def _track(self, frame: Any, persons: list[dict[str, Any]]) -> list[dict[str, Any]]:

        detections = []

        for person in persons:
            x1, y1, x2, y2 = person["bbox"]

            detections.append((
                [x1, y1, x2 - x1, y2 - y1],
                float(person["confidence"]),
                "person"

            ))

        raw_tracks = self.tracker.update_tracks(detections, frame=frame)
        confirmed: list[dict[str, Any]] = []

        for raw_track in raw_tracks:
            if not raw_track.is_confirmed():
                continue

            if getattr(raw_track, "time_since_update", 0) > 0:
                continue

            track_bbox = [float(value) for value in raw_track.to_ltrb()]

            parent = self._best_parent(track_bbox, persons)

            confidence = (
                float(raw_track.det_conf)
                if raw_track.det_conf is not None
                else float(parent["confidence"] if parent else 0.0)
            )

            confirmed.append({
                "track_id": int(raw_track.track_id),
                "bbox": track_bbox,
                "confidence": confidence,


                "weapon_detected": bool(parent and parent["weapon_detected"]),
                "weapon_type": parent["weapon_type"] if parent else None,
                "weapon_confidence": parent["weapon_confidence"] if parent else None
                
            })

        return confirmed


    def _classify_behaviour(self, track: dict[str, Any], now: float, frame_shape: tuple[int, ...]) -> dict[str, Any]:

        track_id = int(track["track_id"])
        history = self._histories.setdefault(track_id, _TrackHistory())
        history.last_seen = now

        bbox = track["bbox"]
        centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)

        frame_height, frame_width = frame_shape[:2]

        normalized_centroid = (centroid[0] / max(float(frame_width), 1.0), centroid[1] / max(float(frame_height), 1.0))

        inside = tuple(
            self._point_in_polygon(normalized_centroid[0], normalized_centroid[1], polygon)
            for polygon in self.zones
        )

        if history.previous_inside is not None:

            for index, is_inside in enumerate(inside):
                was_inside = history.previous_inside[index]
                if is_inside and not was_inside:
                    history.entered_at[index] = now
                elif not is_inside:
                    history.entered_at.pop(index, None)
                if is_inside != was_inside:
                    history.crossings.setdefault(index, deque()).append(now)
        else:
            for index, is_inside in enumerate(inside):
                if is_inside:
                    history.entered_at[index] = now


        history.previous_inside = inside

        crossing_counts: dict[int, int] = {}

        for index, crossing_times in history.crossings.items():
            while crossing_times and now - crossing_times[0] > self.config.scan_time_window_seconds:
                crossing_times.popleft()


            crossing_counts[index] = len(crossing_times)

        loitering_zone = next(
            (
                index
                for index, entered_at in history.entered_at.items()
                if now - entered_at >= self.config.loitering_threshold_seconds
            ),
            None

        )


        perimeter_zone = max(crossing_counts, key=crossing_counts.get, default=None)

        if perimeter_zone is not None and crossing_counts[perimeter_zone] < self.config.scan_crossing_threshold:
            perimeter_zone = None

        if track["weapon_detected"]:
            detection_type = DETECTION_WEAPON
            severity = SEVERITY_CRITICAL
            selected_zone = loitering_zone if loitering_zone is not None else perimeter_zone
        elif perimeter_zone is not None:
            detection_type = DETECTION_PERIMETER_SCAN
            severity = SEVERITY_HIGH
            selected_zone = perimeter_zone
        elif loitering_zone is not None:
            detection_type = DETECTION_LOITERING
            severity = SEVERITY_MEDIUM
            selected_zone = loitering_zone
        else:
            detection_type = DETECTION_HUMAN
            severity = SEVERITY_MEDIUM if track["confidence"] >= 0.75 else SEVERITY_LOW
            selected_zone = next((index for index, value in enumerate(inside) if value), None)


        duration = None
        if selected_zone is not None and selected_zone in history.entered_at:
            duration = max(0.0, now - history.entered_at[selected_zone])

        crossing_count = (
            crossing_counts.get(selected_zone, 0)
            if selected_zone is not None
            else None


        )

        return {
            "detection_type": detection_type,
            "severity": severity,
            "loitering_duration_seconds": duration,
            "scan_crossing_count": crossing_count,
            "zone_id": self.zone_ids[selected_zone]
            if selected_zone is not None and selected_zone < len(self.zone_ids)
            else None


        }

    def _cleanup_histories(self, now: float) -> None:

        expired = [
            track_id
            for track_id, history in self._histories.items()
            if now - history.last_seen > self.config.history_retention_seconds
        ]
        
        for track_id in expired:
            del self._histories[track_id]
