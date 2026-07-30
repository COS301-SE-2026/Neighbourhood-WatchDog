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

class TestLinkProprtyTokenRes:
    def _make_nested_res(self) -> LinkPropertyToken:
        return LinkPropertyToken(**_link_property_token())

    def test_valid_response_with_data(self):
        res = LinkPropertyTokenRes(
            status=200,
            message="Pairing token created",
            data=self._make_nested_res(),
        )

        assert res.status == 200
        assert res.data is not None

    def test_only_status_required(self):
        res = LinkPropertyTokenRes(status=200)

        assert res.status == 200
        assert res.message is None
        assert res.data is None

    def test_missing_status_raises(self):
        with pytest.raises(ValidationError):
            LinkPropertyTokenRes(message="oops")

    def test_invalid_nested_data_raises(self):
        with pytest.raises(ValidationError):
            LinkPropertyTokenRes(
                status=200,
                message="ok",
                data={**_link_property_token(), "expires_at": "not-a-datetime"},
            )

class TestEdgeAgentsCredentialsSchema:
    def _make_camera(self) -> CameraRes:
        return CameraRes(**_camera_res())

    def test_valid_fields(self):
        data = _edge_agents_credentials(cameras=[self._make_camera()])
        schema = EdgeAgentsCredentialsSchema(**data)

        assert schema.property_id == data["property_id"]
        assert schema.address == data["address"]
        assert schema.api_key == data["api_key"]
        assert len(schema.cameras) == 1
        assert schema.created_at == data["created_at"]

    def test_missing_property_id_raises(self):
        data = _edge_agents_credentials()
        del data["address"]

        with pytest.raises(ValidationError):
            EdgeAgentsCredentialsSchema(**data)

    def test_missing_api_key_raises(self):
        data = _edge_agents_credentials()
        del data["api_key"]

        with pytest.raises(ValidationError):
            EdgeAgentsCredentialsSchema(**data)

    def test_missing_cameras_raises(self):
        data = _edge_agents_credentials()
        del data["cameras"]

        with pytest.raises(ValidationError):
            EdgeAgentsCredentialsSchema(**data)

    def test_missing_created_at_raises(self):
        data = _edge_agents_credentials()
        del data["created_at"]

        with pytest.raises(ValidationError):
            EdgeAgentsCredentialsSchema(**data)

    def test_empty_cameras_list_is_allowed(self):
        data = _edge_agents_credentials(cameras=[])
        schema = EdgeAgentsCredentialsSchema(**data)

        assert schema.cameras == []

    def test_invalid_camera_in_list_raises(self):
        data = _edge_agents_credentials(cameras=[{**_camera_res(), "id": "not-a-uuid"}])

        with pytest.raises(ValidationError):
            EdgeAgentsCredentialsSchema(**data)

class TestEdgeAgentsCredentialsRes:
    def _make_nested_res(self) -> EdgeAgentsCredentialsSchema:
        return EdgeAgentsCredentialsSchema(**_edge_agents_credentials())

    def test_valid_response_with_data(self):
        res = EdgeAgentsCredentialsRes(
            status=200,
            message="Agent paired",
            data=self._make_nested_res(),
        )

        assert res.status == 200
        assert res.data is not None

    def test_only_status_required(self):
        res = EdgeAgentsCredentialsRes(status=200)

        assert res.status == 200
        assert res.message is None
        assert res.data is None

    def test_missing_status_raises(self):
        with pytest.raises(ValidationError):
            EdgeAgentsCredentialsRes(message="oops")

    def test_invalid_nested_data_raises(self):
        with pytest.raises(ValidationError):
            EdgeAgentsCredentialsRes(
                status=200,
                message="ok",
                data={**_edge_agents_credentials(), "property_id": "not-a-uuid"},
            )