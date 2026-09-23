import numpy as np

from pipeline.processing.cascaded_pipeline import (
    CascadedPipeline,
    CascadedPipelineConfig,
)


class FakeBox:
    def __init__(self, bbox, confidence, class_id):
        self.xyxy = np.array([bbox], dtype=float)
        self.conf = np.array([confidence], dtype=float)
        self.cls = np.array([class_id], dtype=float)


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeModel:
    def __init__(self, results, names=None):
        self.results = results
        self.names = names or {
            0: "person",
            1: "knife",
        }
        self.calls = []

    def predict(self, frame, **kwargs):
        self.calls.append((frame.shape, kwargs))
        return [FakeResult(self.results)]


class FakeTrack:
    def __init__(self, track_id, bbox, confidence=0.9, feature=None):
        self.track_id = track_id
        self._bbox = bbox
        self.det_conf = confidence
        self.time_since_update = 0
        self._feature = feature

    def get_feature(self):
        return self._feature

    def is_confirmed(self):
        return True

    def to_ltrb(self):
        return np.array(self._bbox, dtype=float)


class FakeTracker:
    def __init__(self, tracks):
        self.tracks = tracks
        self.calls = 0

    def update_tracks(self, detections, frame):
        self.calls += 1
        return self.tracks[self.calls - 1] if isinstance(self.tracks[0], list) else self.tracks


def test_weapon_model_is_not_called_when_gate_finds_no_person():
    person_model = FakeModel([])
    weapon_model = FakeModel([FakeBox([0, 0, 5, 5], 0.99, 1)])
    tracker = FakeTracker([])
    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=weapon_model,
        tracker=tracker,
    )

    result = pipeline.process_frame(np.zeros((100, 200, 3), dtype=np.uint8))

    assert result.tracks == []
    assert result.events == []
    assert len(person_model.calls) == 1
    assert len(weapon_model.calls) == 0
    assert tracker.calls == 0


def test_weapon_inference_receives_full_frame_and_is_attached_to_parent_track():
    person_model = FakeModel([FakeBox([10, 20, 50, 70], 0.91, 0)])
    weapon_model = FakeModel([FakeBox([12, 23, 22, 35], 0.88, 1)])
    tracker = FakeTracker([FakeTrack(7, [10, 20, 50, 70])])
    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=weapon_model,
        tracker=tracker,
        config=CascadedPipelineConfig(n_init=1),
    )

    result = pipeline.process_frame(np.zeros((100, 200, 3), dtype=np.uint8))

    assert weapon_model.calls[0][0] == (100, 200, 3)
    assert result.tracks[0]["track_id"] == 7
    assert result.tracks[0]["weapon_detected"] is True
    assert result.tracks[0]["weapon_type"] == "knife"
    assert result.events[0]["detection_type"] == "WEAPON_DETECTED"
    assert result.events[0]["severity"] == "CRITICAL"


def test_loitering_is_derived_from_track_history():
    person_model = FakeModel([FakeBox([10, 10, 30, 30], 0.90, 0)])
    weapon_model = FakeModel([])
    tracker = FakeTracker([
        [FakeTrack(3, [10, 10, 30, 30])],
        [FakeTrack(3, [10, 10, 30, 30])],
    ])
    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=weapon_model,
        zones=[[[0.0, 0.0], [0.5, 0.0], [0.5, 0.5], [0.0, 0.5]]],
        zone_ids=["zone-1"],
        tracker=tracker,
        config=CascadedPipelineConfig(
            loitering_threshold_seconds=5.0,
            n_init=1,
        ),
    )
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    first = pipeline.process_frame(frame, timestamp=0.0)
    second = pipeline.process_frame(frame, timestamp=6.0)

    assert first.events[0]["detection_type"] == "HUMAN_PRESENCE"
    assert second.events[0]["detection_type"] == "LOITERING"
    assert second.events[0]["severity"] == "MEDIUM"
    assert second.events[0]["zone_id"] == "zone-1"
    assert second.events[0]["loitering_duration_seconds"] == 6.0


def test_best_parent_returns_none_when_no_person_overlaps_track():

    track_bbox = [100, 100, 140, 160]

    persons = [
        {
            "bbox": [0, 0, 20, 20],
            "confidence": 0.95,
            "weapon_detected": True,
            "weapon_type": "knife",
            "weapon_confidence": 0.90

        },
        {
            "bbox": [200, 200, 240, 260],
            "confidence": 0.88,
            "weapon_detected": False,
            "weapon_type": None,
            "weapon_confidence": None

        }


    ]

    assert CascadedPipeline._best_parent(track_bbox, persons) is None



def test_confirmed_track_exposes_normalized_appearance_embedding():
    person_model = FakeModel([FakeBox([10, 20, 50, 70], 0.91, 0)])

    weapon_model = FakeModel([])

    tracker = FakeTracker([
        FakeTrack(
            track_id=7,
            bbox=[10, 20, 50, 70],
            feature=[3.0, 4.0]

        )

    ])

    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=weapon_model,
        tracker=tracker,
        config=CascadedPipelineConfig(n_init=1) 

    )

    result = pipeline.process_frame(np.zeros((100, 200, 3), dtype=np.uint8))

    assert result.appearance_embeddings[7] == [0.6, 0.8]
    assert "appearance_embedding" not in result.tracks[0]


def test_pipeline_preserves_camera_local_id_after_short_occlusion():
    person_model = FakeModel([FakeBox([10, 20, 50, 70], 0.91, 0)])

    weapon_model = FakeModel([])

    tracker = FakeTracker([
        [FakeTrack(7, [10, 20, 50, 70])],
        [],
        [FakeTrack(7, [12, 22, 52, 72])]
        
    ])

    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=weapon_model,
        tracker=tracker,
        config=CascadedPipelineConfig(
            max_age=2,
            n_init=1

        )

    )

    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    first = pipeline.process_frame(frame, timestamp=0.0)
    during_occlusion = pipeline.process_frame(frame, timestamp=1.0)
    recovered = pipeline.process_frame(frame, timestamp=2.0)

    assert [track["track_id"] for track in first.tracks] == [7]
    assert during_occlusion.tracks == []
    assert [track["track_id"] for track in recovered.tracks] == [7]


def test_weapon_outside_person_is_not_attached():
    person_model = FakeModel([FakeBox([10, 20, 50, 70], 0.91, 0)])
    weapon_model = FakeModel([FakeBox([150, 10, 180, 30], 0.88, 1)])
    tracker = FakeTracker([FakeTrack(7, [10, 20, 50, 70])])

    pipeline = CascadedPipeline(
        person_model=person_model,
        weapon_model=weapon_model,
        tracker=tracker,
        config=CascadedPipelineConfig(n_init=1),
    )

    result = pipeline.process_frame(
        np.zeros((100, 200, 3), dtype=np.uint8)
    )

    assert result.tracks[0]["weapon_detected"] is False
    assert result.events[0]["detection_type"] == "HUMAN_PRESENCE"