from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.alert import AlertRes, AcknowledgeAlertRes, ListAlertsRes, Pagination

def _make_alert_res(**overrides):
    base = {
        "id": uuid4(),
        "camera_id": uuid4(),
        "detection_event_id": uuid4(),
        "status": "OPEN",
        "resolved_by": None,
        "resolved_at": None,
        "created_at": datetime.now(timezone.utc),
        "detection_type": "HUMAN_PRESENCE",
        "confidence_score": 0.85,
        "thumbnail_url": None,
    }
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
        assert alert.confidence_score == pytest.approx(0.85)
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

class TestAcknowledgeAlertRes:
    def _make_nested_alert(self):
        return AlertRes(**_make_alert_res(status="ACKNOWLEDGED"))

    def test_valid_response_with_data(self):
        """Happy path: status, message, and nested AlertRes all present"""
        alert = self._make_nested_alert()
        res = AcknowledgeAlertRes(
            status=200,
            message="Alert acknowledged",
            data=alert,
        )

        assert res.status == 200
        assert res.message == "Alert acknowledged"
        assert res.data is not None
        assert res.data.status == "ACKNOWLEDGED"

    def test_only_status_required(self):
        """message and data are optional and default to None"""
        res = AcknowledgeAlertRes(status=200)

        assert res.status == 200
        assert res.message is None
        assert res.data is None

    def test_error_response_without_data(self):
        """4xx/5xx responses carry no data"""
        res = AcknowledgeAlertRes(status=404, message="Alert not found")

        assert res.status == 404
        assert res.message == "Alert not found"
        assert res.data is None

    def test_missing_status_raises_validation_error(self):
        """status is required"""
        with pytest.raises(ValidationError):
            AcknowledgeAlertRes(message="oops")

    def test_invalid_nested_data_raises_validation_error(self):
        """Passing a plain dict with missing required fields as data must raise error"""
        with pytest.raises(ValidationError):
            AcknowledgeAlertRes(status=200, data={"status": "OPEN"})

class TestListAlertsRes:
    def _make_alert(self, status: str = "OPEN") -> AlertRes:
        return AlertRes(**_make_alert_res(status=status))

    def test_valid_response_with_multiple_alerts(self):
        """Happy path: list of AlertRes objects"""
        alerts = [self._make_alert("OPEN"), self._make_alert("ACKNOWLEDGED")]
        res = ListAlertsRes(status=200, message="OK", data=alerts)

        assert res.status == 200
        assert len(res.data) == 2
        assert res.data[0].status == "OPEN"
        assert res.data[1].status == "ACKNOWLEDGED"

    def test_empty_list_is_valid(self):
        """An empty list is a legitimate response (there are no active alerts)"""
        res = ListAlertsRes(status=200, data=[])

        assert res.data == []

    def test_data_none_by_default(self):
        """message and data are optional"""
        res = ListAlertsRes(status=200)

        assert res.message is None
        assert res.data is None

    def test_missing_status_raises_validation_error(self):
        """status is required"""
        with pytest.raises(ValidationError):
            ListAlertsRes(data=[])

    def test_invalid_item_in_list_raises_validation_error(self):
        """Each item in data must be a valid AlertRes"""
        with pytest.raises(ValidationError):
            ListAlertsRes(status=200, data=["not-an-alert-res"])

    def test_pagination_none_by_default(self):
        """Pagination is optional"""
        res = ListAlertsRes(status=200, data=[])
        assert res.pagination is None

    def test_with_pagination(self):
        pagination = Pagination(total=2, limit=25, offset=0, has_more=False)
        res = ListAlertsRes(status=200, data=[], pagination=pagination)
        assert res.pagination.total == 2
        assert res.pagination.has_more is False

class TestPagination:
    def test_valid_pagination(self):
        p = Pagination(total=42
                       , limit=25
                       , offset=0
                       , has_more=True)
        
        assert p.total == 42
        assert p.limit == 25
        assert p.offset == 0
        assert p.has_more

    def test_missin_fields_raises_validation_error(self):
        with pytest.raises(ValidationError):
            Pagination(total=42
                       , offset=0
                       , has_more=True)