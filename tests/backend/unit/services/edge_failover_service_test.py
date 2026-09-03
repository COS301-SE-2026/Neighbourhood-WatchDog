import base64
import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services import edge_failover_service as service


CAMERA_ID = uuid.uuid4()
PROPERTY_ID = uuid.uuid4()


def make_db(*results):
    db = MagicMock()
    db.execute = AsyncMock(side_effect=list(results))
    return db


def camera_result(cameras):
    result = MagicMock()
    result.scalars.return_value.all.return_value = list(cameras)
    return result


def heartbeat_result(rows):
    result = MagicMock()
    result.all.return_value = list(rows)
    return result


def make_camera(*, enabled=True, property_id=PROPERTY_ID):
    return SimpleNamespace(
        id=CAMERA_ID,
        property_id=property_id,
        enabled=enabled,
        rtsp_url="encrypted-value",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestPublishCredentials:
    def test_missing_master_key_is_rejected(self, monkeypatch):
        monkeypatch.delenv("MEDIAMTX_PUBLISH_MASTER_KEY", raising=False)
        with pytest.raises(RuntimeError, match="not configured"):
            service.camera_publish_credentials(CAMERA_ID)

    def test_credentials_are_deterministic_for_camera(self, monkeypatch):
        master_key = "test-master-key"
        monkeypatch.setenv("MEDIAMTX_PUBLISH_MASTER_KEY", master_key)

        username, password = service.camera_publish_credentials(CAMERA_ID)
        camera_text = str(CAMERA_ID)
        digest = hmac.new(
            master_key.encode(), camera_text.encode(), hashlib.sha256
        ).digest()
        expected_password = base64.urlsafe_b64encode(digest).decode().rstrip("=")

        assert username == f"camera-{CAMERA_ID}"
        assert password == expected_password
        assert service.camera_publish_credentials(str(CAMERA_ID)) == (
            username,
            password,
        )


class TestFailoverControllerToken:
    def test_missing_configured_token_is_rejected(self, monkeypatch):
        monkeypatch.setattr(service, "FAILOVER_CONTROLLER_TOKEN", "")
        with pytest.raises(RuntimeError, match="not configured"):
            service.require_failover_controller_token("anything")

    def test_missing_or_wrong_token_returns_401(self, monkeypatch):
        monkeypatch.setattr(service, "FAILOVER_CONTROLLER_TOKEN", "expected")

        for provided in (None, "wrong"):
            with pytest.raises(HTTPException) as exc:
                service.require_failover_controller_token(provided)
            assert exc.value.status_code == 401
            assert exc.value.detail == "Invalid failover controller token"

    def test_correct_token_is_accepted(self, monkeypatch):
        monkeypatch.setattr(service, "FAILOVER_CONTROLLER_TOKEN", "expected")
        assert service.require_failover_controller_token("expected") is None


class TestListFailoverCameras:
    @pytest.mark.asyncio
    async def test_empty_camera_result_returns_empty_data(self, monkeypatch):
        monkeypatch.setenv("MEDIAMTX_PUBLISH_MASTER_KEY", "test-master-key")
        db = make_db(camera_result([]))

        response = await service.list_failover_cameras(db)

        assert response.data == []
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_maps_camera_credentials_and_latest_heartbeat(self, monkeypatch):
        monkeypatch.setenv("MEDIAMTX_PUBLISH_MASTER_KEY", "test-master-key")
        camera = make_camera()
        last_seen = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
        db = make_db(
            camera_result([camera]),
            heartbeat_result([(PROPERTY_ID, last_seen)]),
        )

        with (
            patch.object(service, "decrypt_rtsp_url", return_value="rtsp://safe-url"),
            patch.object(
                service,
                "camera_publish_credentials",
                return_value=("camera-user", "camera-password"),
            ),
        ):
            response = await service.list_failover_cameras(db)

        assert len(response.data) == 1
        item = response.data[0]
        assert item.id == CAMERA_ID
        assert item.property_id == PROPERTY_ID
        assert item.enabled is True
        assert item.rtsp_url == "rtsp://safe-url"
        assert item.publish_username == "camera-user"
        assert item.publish_password == "camera-password"
        assert item.edge_agent_last_seen_at == last_seen
        assert db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_camera_without_heartbeat_gets_none(self, monkeypatch):
        monkeypatch.setenv("MEDIAMTX_PUBLISH_MASTER_KEY", "test-master-key")
        camera = make_camera(property_id=PROPERTY_ID)
        db = make_db(
            camera_result([camera]),
            heartbeat_result([]),
        )

        with (
            patch.object(service, "decrypt_rtsp_url", return_value="rtsp://safe-url"),
            patch.object(
                service,
                "camera_publish_credentials",
                return_value=("camera-user", "camera-password"),
            ),
        ):
            response = await service.list_failover_cameras(db)

        assert response.data[0].edge_agent_last_seen_at is None

    @pytest.mark.asyncio
    async def test_decryption_error_is_not_silently_hidden(self, monkeypatch):
        monkeypatch.setenv("MEDIAMTX_PUBLISH_MASTER_KEY", "test-master-key")
        db = make_db(
            camera_result([make_camera()]),
            heartbeat_result([]),
        )

        with patch.object(
            service,
            "decrypt_rtsp_url",
            side_effect=ValueError("invalid ciphertext"),
        ):
            with pytest.raises(ValueError, match="invalid ciphertext"):
                await service.list_failover_cameras(db)