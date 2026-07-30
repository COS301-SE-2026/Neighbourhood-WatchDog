from pydantic import ValidationError
import pytest
from uuid import uuid4
from app.schemas.camera_settings import CameraSettingsResponse, ZoneResponse, UpdateCameraSettingsRequest, ZonePoint, CreateZoneRequest

def _zone_response(**overrides):
    base = {
        "id": uuid4(),
        "camera_id": uuid4(),
        "name": "Front Door",
        "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
    }
    base.update(overrides)
    return base

class TestZonePoint:
    def test_valid_point(self):
        point = ZonePoint(x=0.5, y=0.5)

        assert point.x == 0.5
        assert point.y == 0.5

    def test_x_at_lower_boundary(self):
        point = ZonePoint(x=0.0, y=0.5)

        assert point.x == 0.0

    def test_x_at_upper_boundary(self):
        point = ZonePoint(x=1.0, y=0.5)

        assert point.x == 1.0

    def test_x_above_lower_boundary_raises(self):
        with pytest.raises(ValidationError):
            ZonePoint(x=1.1, y=0.5)

    def test_y_below_lower_boundary_raises(self):
        with pytest.raises(ValidationError):
            ZonePoint(x=0.5, y=-0.1)

    def test_y_above_upper_boundary_raises(self):
        with pytest.raises(ValidationError):
            ZonePoint(x=0.5, y=1.1)

    def test_missing_x_raises(self):
        with pytest.raises(ValidationError):
            ZonePoint(y=0.5)

    def test_missing_y_raises(self):
        with pytest.raises(ValidationError):
            ZonePoint(x=0.5)

class TestCreateZoneReq:
    def test_valid_req(self):
        req = CreateZoneRequest(name="Backyard", polygon=[[0.0, 0.0], [1.0, 1.0]])
        assert req.name == "Backyard"
        assert req.polygon == [[0.0, 0.0], [1.0, 1.0]]

    def test_name_defaults_to_zone(self):
        req = CreateZoneRequest(polygon=[[0.0, 0.0], [1.0, 1.0]])
        assert req.name == "Zone"

    def test_empty_polygon_list_is_allowed(self):
        req = CreateZoneRequest(polygon=[])
        assert req.polygon == []

    def test_missing_polygon_raises(self):
        with pytest.raises(ValidationError):
            CreateZoneRequest(name="Backyard")

class TestZoneRes:
    def test_valid_fields(self):
        data = _zone_response()
        res = ZoneResponse(**data)

        assert res.id == data["id"]
        assert res.camera_id == data["camera_id"]
        assert res.name == data["name"]
        assert res.polygon == data["polygon"]

    def test_missing_id_raises(self):
        data = _zone_response()
        del data["id"]

        with pytest.raises(ValidationError):
            ZoneResponse(**data)

    def test_missing_camera_id_raises(self):
        data = _zone_response()
        del data["camera_id"]

        with pytest.raises(ValidationError):
            ZoneResponse(**data)

    def test_missing_name_raises(self):
        data = _zone_response()
        del data["name"]

        with pytest.raises(ValidationError):
            ZoneResponse(**data)

    def test_missing_polygon_raises(self):
        data = _zone_response()
        del data["polygon"]

        with pytest.raises(ValidationError):
            ZoneResponse(**data)

    def test_from_attributes_config_present(self):
        """model_config should allow construction from ORM objects"""
        assert ZoneResponse.model_config.get("from_attributes") is True

class TestUpdateCameraSettingsReq:
    def test_valid_threshold(self):
        req = UpdateCameraSettingsRequest(confidence_threshold=0.75)
        assert req.confidence_threshold == 0.75

    def test_confidence_threshold_defaults_to_none(self):
        req = UpdateCameraSettingsRequest()
        assert req.confidence_threshold is None

    def test_threshold_at_lower(self):
        req = UpdateCameraSettingsRequest(confidence_threshold=0.0)
        assert req.confidence_threshold == 0.0

    def test_threshold_at_upper(self):
        req = UpdateCameraSettingsRequest(confidence_threshold=1.0)
        assert req.confidence_threshold == 1.0

    def test_threshold_below_boundary_raises(self):
        with pytest.raises(ValidationError):
            UpdateCameraSettingsRequest(confidence_threshold=-0.1)

    def test_threshold_above_boundary_raises(self):
        with pytest.raises(ValidationError):
            UpdateCameraSettingsRequest(confidence_threshold=1.1)

class TestCameraSettingsRes:
    def _make_zone(self) -> ZoneResponse:
        return ZoneResponse(**_zone_response())

    def test_valid_fields(self):
        res = CameraSettingsResponse(
            camera_id=uuid4(),
            confidence_threshold=0.65,
            zones=[self._make_zone()],
        )

        assert res.confidence_threshold == 0.65
        assert len(res.zones) == 1

    def test_missing_camera_id_raises(self):
        with pytest.raises(ValidationError):
            CameraSettingsResponse(confidence_threshold=0.65, zones=[])

    def test_missing_confidence_threshold_raises(self):
        with pytest.raises(ValidationError):
            CameraSettingsResponse(camera_id=uuid4(), zones=[])

    def test_missing_zones_raises(self):
        with pytest.raises(ValidationError):
            CameraSettingsResponse(camera_id=uuid4(), confidence_threshold=0.65)

    def test_empty_zones_list_is_allowed(self):
        with pytest.raises(ValidationError):
            CameraSettingsResponse(camera_id=uuid4(), confidence_threshold=0.65, zones=[{**_zone_response(), "id": "not-a-uuid"}],)       