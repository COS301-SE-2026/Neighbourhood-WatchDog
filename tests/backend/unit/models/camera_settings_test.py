from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
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
        req = CreateZoneRequest(name="Backyard", polygon=[[0.0, 0.0], [1.0, 1.0]])
        assert req.name == "Zone"

    def test_empty_polygon_list_is_allowed(self):
        req = CreateZoneRequest(polygon=[])
        assert req.polygon == []

    def test_missing_polygon_raises(self):
        with pytest.raises(ValidationError):
            CreateZoneRequest(name="Backyard")
        

    
        