from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.alert import AlertRes, AcknowledgeAlertRes, ListAlertsRes

def _make_alert_res(**overrides):
    base = dict(
        id=uuid4(),
        camera_id=uuid4(),
        detection_event_id=uuid4(),
        status="OPEN",
        resolved_by=None,
        resolved_at=None,
        created_at=datetime.now(timezone.utc),
        detection_type="HUMAN_PRESENCE",
        confidence_score=0.85,
        thumbnail_url=None,
    )
    base.update(overrides)
    return base

class TestAlertRes:
    def test_valid_open_alert(self):
        """Happy path: all required fields"""
        data = _make_alert_res()
        alert = AlertRes(**data)

        assert alert.id == data["id"]
        assert alert.camera_id == data["camera_id"]
        assert alert.detection_event_id == data["detection_event_id"]
        assert alert.status == "OPEN"
        assert alert.resolved_by is None
        assert alert.resolved_at is None
        assert alert.detection_type == "HUMAN_PRESENCE"
        assert alert.confidence_score == 0.85
        assert alert.thumbnail_url is None

    def test_acknowledged_alert_with_resolved_by(self):
        """Acknowledged alert can carry a resolver UUID"""
        data = _make_alert_res(
            status="ACKNOWLEDGED",
            resolved_by=uuid4(),
            resolved_at=datetime.now(timezone.utc),
        )
        alert = AlertRes(**data)

        assert alert.status == "ACKNOWLEDGED"
        assert alert.resolved_by is not None
        assert alert.resolved_at is not None

    def test_optional_fields_default_to_none(self):
        """detection_type, confidence_score, thumbnail_url are all optional"""
        data = _make_alert_res(
            detection_type=None,
            confidence_score=None,
            thumbnail_url=None,
        )
        alert = AlertRes(**data)

        assert alert.detection_type is None
        assert alert.confidence_score is None
        assert alert.thumbnail_url is None

    def test_with_thumbnail_url(self):
        """thumbnail_url accepts a string when provided"""
        data = _make_alert_res(thumbnail_url="https://cdn.example.com/thumb.jpg")
        alert = AlertRes(**data)

        assert alert.thumbnail_url == "https://cdn.example.com/thumb.jpg"

    def test_missing_id_raises_validation_error(self):
        """id is required, omitting it must raise error"""
        data = _make_alert_res()
        del data["id"]

        with pytest.raises(ValidationError):
            AlertRes(**data)

    def test_missing_camera_id_raises_validation_error(self):
        """camera_id is required"""
        data = _make_alert_res()
        del data["camera_id"]

        with pytest.raises(ValidationError):
            AlertRes(**data)

    def test_missing_detection_event_id_raises_validation_error(self):
        """detection_event_id is required"""
        data = _make_alert_res()
        del data["detection_event_id"]

        with pytest.raises(ValidationError):
            AlertRes(**data)

    def test_missing_status_raises_validation_error(self):
        """status is required"""
        data = _make_alert_res()
        del data["status"]

        with pytest.raises(ValidationError):
            AlertRes(**data)

    def test_missing_created_at_raises_validation_error(self):
        """created_at is required"""
        data = _make_alert_res()
        del data["created_at"]

        with pytest.raises(ValidationError):
            AlertRes(**data)

    def test_invalid_uuid_for_id_raises_validation_error(self):
        """Non-UUID value for id must be rejected"""
        data = _make_alert_res(id="not-a-uuid")

        with pytest.raises(ValidationError):
            AlertRes(**data)

    def test_invalid_uuid_for_resolved_by_raises_validation_error(self):
        """Non-UUID value for resolved_by must be rejected"""
        data = _make_alert_res(resolved_by="bad-uuid")

        with pytest.raises(ValidationError):
            AlertRes(**data)

    def test_from_attributes_config_present(self):
        """model_config should allow construction from ORM objects"""
        assert AlertRes.model_config.get("from_attributes") is True