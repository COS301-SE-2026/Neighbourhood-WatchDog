from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.services.pairing_token import LinkPropertyToken, LinkPropertyTokenRes, EdgeAgentsCredentialsRes, EdgeAgentsCredentialsSchema
from app.schemas.camera import CameraRes
from app.models.camera import CameraVisibilityEnum

def _camera_res(**overrides):
    base = {
        "id": uuid4(),
        "property_id": uuid4(),
        "neighbourhood_id": uuid4(),
        "name": "Front Door Cam",
        "visibility": list(CameraVisibilityEnum)[0],
        "location": "Front Door",
        "rtsp_url": "rtsp://example.com/stream",
        "enabled": True,
        "created_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base

def _link_property_token(**overrides):
    base = {
        "token": "abc123token",
        "expires_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base

def _edge_agents_credentials(**overrides):
    base = {
        "property_id": uuid4(),
        "address": "123 Main St",
        "api_key": "super-secret-key",
        "cameras": [],
        "created_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base

class TestLinkPropertyToken:
    def test_valid_fields(self):
        data = _link_property_token()
        token = LinkPropertyToken(**data)

        assert token.token == data["token"]
        assert token.expires_at == data["expires_at"]

    def test_missing_token_raises(self):
        data = _link_property_token()
        del data["token"]

        with pytest.raises(ValidationError):
            LinkPropertyToken(**data)

    def test_missing_expires_at_raises(self):
        data = _link_property_token()
        del data["expires_at"]

        with pytest.raises(ValidationError):
            LinkPropertyToken(**data)