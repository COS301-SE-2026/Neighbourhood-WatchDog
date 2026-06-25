from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.detection import DetectionIngestReq, DetectionEventRes, DetectionIngestRes

VALID_DETECTION_TYPES = [
    "HUMAN_PRESENCE",
    "LOITERING",
    "PERIMETER_SCAN",
    "WEAPON_DETECTED",
    "FALL_DETECTED",
]

def _make_ingest_req(**overrides):
    base = dict(
        camera_id=uuid4(),
        frame_timestamp=datetime.now(timezone.utc),
        detection_type="HUMAN_PRESENCE",
        confidence_score=0.75,
        thumbnail_url=None,
        zone_id=None,
    )
    base.update(overrides)
    return base


def _make_event_res(**overrides):
    base = dict(
        id=uuid4(),
        camera_id=uuid4(),
        frame_timestamp=datetime.now(timezone.utc),
        detection_type="HUMAN_PRESENCE",
        confidence_score=0.75,
        thumbnail_url=None,
        processed=False,
    )
    base.update(overrides)
    return base

class TestDetectionIngestReq:
    def test_valid_request(self):
        """Happy path: all fields valid"""
        data = _make_ingest_req()
        req = DetectionIngestReq(**data)

        assert req.camera_id == data["camera_id"]
        assert req.detection_type == "HUMAN_PRESENCE"
        assert req.confidence_score == 0.75
        assert req.thumbnail_url is None
        assert req.zone_id is None

    @pytest.mark.parametrize("detection_type", VALID_DETECTION_TYPES)
    def test_all_valid_detection_types_accepted(self, detection_type):
        """Every allowed detection_type string should pass validation"""
        req = DetectionIngestReq(**_make_ingest_req(detection_type=detection_type))
        assert req.detection_type == detection_type

    def test_invalid_detection_type_raises_validation_error(self):
        """Unknown detection_type must be rejected"""
        with pytest.raises(ValidationError):
            DetectionIngestReq(**_make_ingest_req(detection_type="ALIEN_SPOTTED"))

    def test_empty_detection_type_raises_validation_error(self):
        """Empty string is not a valid detection_type"""
        with pytest.raises(ValidationError):
            DetectionIngestReq(**_make_ingest_req(detection_type=""))

    def test_confidence_score_boundary_zero(self):
        """0.0 is a valid lower boundary"""
        req = DetectionIngestReq(**_make_ingest_req(confidence_score=0.0))
        assert req.confidence_score == 0.0

    def test_confidence_score_boundary_one(self):
        """1.0 is a valid upper boundary"""
        req = DetectionIngestReq(**_make_ingest_req(confidence_score=1.0))
        assert req.confidence_score == 1.0

    def test_confidence_score_above_range_raises_validation_error(self):
        """Scores above 1.0 must be rejected"""
        with pytest.raises(ValidationError):
            DetectionIngestReq(**_make_ingest_req(confidence_score=1.01))

    def test_confidence_score_below_range_raises_validation_error(self):
        """Negative scores must be rejected"""
        with pytest.raises(ValidationError):
            DetectionIngestReq(**_make_ingest_req(confidence_score=-0.1))

    def test_confidence_score_far_out_of_range_raises_validation_error(self):
        """Out of range values (e.g. 150) must be rejected"""
        with pytest.raises(ValidationError):
            DetectionIngestReq(**_make_ingest_req(confidence_score=150))

    def test_optional_zone_id_accepted(self):
        """zone_id is optional and accepts a valid UUID"""
        zone = uuid4()
        req = DetectionIngestReq(**_make_ingest_req(zone_id=zone))
        assert req.zone_id == zone

    def test_optional_thumbnail_url_accepted(self):
        """thumbnail_url is optional and accepts a string"""
        req = DetectionIngestReq(**_make_ingest_req(thumbnail_url="https://cdn.example.com/frame.jpg"))
        assert req.thumbnail_url == "https://cdn.example.com/frame.jpg"

    def test_missing_camera_id_raises_validation_error(self):
        """camera_id is required"""
        data = _make_ingest_req()
        del data["camera_id"]

        with pytest.raises(ValidationError):
            DetectionIngestReq(**data)

    def test_invalid_camera_id_raises_validation_error(self):
        """Non-UUID camera_id must be rejected"""
        with pytest.raises(ValidationError):
            DetectionIngestReq(**_make_ingest_req(camera_id="not-a-uuid"))

    def test_missing_frame_timestamp_raises_validation_error(self):
        """frame_timestamp is required"""
        data = _make_ingest_req()
        del data["frame_timestamp"]

        with pytest.raises(ValidationError):
            DetectionIngestReq(**data)

    def test_missing_confidence_score_raises_validation_error(self):
        """confidence_score is required"""
        data = _make_ingest_req()
        del data["confidence_score"]

        with pytest.raises(ValidationError):
            DetectionIngestReq(**data)

class TestDetectionEventRes:
    def test_valid_unprocessed_event(self):
        """Happy path: processed=False, no thumbnail"""
        data = _make_event_res(processed=False)
        res = DetectionEventRes(**data)

        assert res.id == data["id"]
        assert res.camera_id == data["camera_id"]
        assert res.detection_type == "HUMAN_PRESENCE"
        assert res.confidence_score == 0.75
        assert res.processed is False
        assert res.thumbnail_url is None

    def test_valid_processed_event(self):
        """processed=True should be accepted"""
        res = DetectionEventRes(**_make_event_res(processed=True))
        assert res.processed is True

    def test_with_thumbnail_url(self):
        """thumbnail_url is optional and accepts a string"""
        res = DetectionEventRes(**_make_event_res(thumbnail_url="https://cdn.example.com/thumb.jpg"))
        assert res.thumbnail_url == "https://cdn.example.com/thumb.jpg"

    def test_missing_id_raises_validation_error(self):
        data = _make_event_res()
        del data["id"]

        with pytest.raises(ValidationError):
            DetectionEventRes(**data)

    def test_missing_camera_id_raises_validation_error(self):
        data = _make_event_res()
        del data["camera_id"]

        with pytest.raises(ValidationError):
            DetectionEventRes(**data)

    def test_missing_frame_timestamp_raises_validation_error(self):
        data = _make_event_res()
        del data["frame_timestamp"]

        with pytest.raises(ValidationError):
            DetectionEventRes(**data)

    def test_missing_detection_type_raises_validation_error(self):
        data = _make_event_res()
        del data["detection_type"]

        with pytest.raises(ValidationError):
            DetectionEventRes(**data)

    def test_missing_confidence_score_raises_validation_error(self):
        data = _make_event_res()
        del data["confidence_score"]

        with pytest.raises(ValidationError):
            DetectionEventRes(**data)

    def test_missing_processed_raises_validation_error(self):
        data = _make_event_res()
        del data["processed"]

        with pytest.raises(ValidationError):
            DetectionEventRes(**data)

    def test_invalid_uuid_raises_validation_error(self):
        with pytest.raises(ValidationError):
            DetectionEventRes(**_make_event_res(id="not-a-uuid"))

    def test_from_attributes_config_present(self):
        """model_config should allow construction from ORM objects"""
        assert DetectionEventRes.model_config.get("from_attributes") is True