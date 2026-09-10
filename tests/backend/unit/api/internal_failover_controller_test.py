from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.internal_failover import failover_cameras
from app.schemas.edge_failover import FailoverCameraRes, FailoverCamerasRes


DB = Mock()
FAILOVER_TOKEN = "expected-failover-token"
CAMERA_ID = uuid4()
PROPERTY_ID = uuid4()
LAST_SEEN_AT = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


def make_failover_camera():
    return FailoverCameraRes(
        id=CAMERA_ID,
        property_id=PROPERTY_ID,
        enabled=True,
        rtsp_url="rtsp://safe-camera-url",
        publish_username="camera-user",
        publish_password="camera-password",
        edge_agent_last_seen_at=LAST_SEEN_AT,
    )


def make_failover_response():
    return FailoverCamerasRes(
        data=[make_failover_camera()],
    )


@pytest.mark.asyncio
async def test_failover_cameras_validates_token_and_returns_cameras():
    expected_response = make_failover_response()

    with (
        patch(
            "app.api.controllers.internal_failover.require_failover_controller_token",
            return_value=None,
        ) as require_token,
        patch(
            "app.api.controllers.internal_failover.list_failover_cameras",
            new=AsyncMock(return_value=expected_response),
        ) as list_cameras,
    ):
        response = await failover_cameras(
            db=DB,
            x_failover_token=FAILOVER_TOKEN,
        )

    assert isinstance(response, FailoverCamerasRes)
    assert response == expected_response
    assert response.data[0].id == CAMERA_ID
    assert response.data[0].property_id == PROPERTY_ID
    assert response.data[0].enabled is True
    assert response.data[0].rtsp_url == "rtsp://safe-camera-url"
    assert response.data[0].publish_username == "camera-user"
    assert response.data[0].publish_password == "camera-password"
    assert response.data[0].edge_agent_last_seen_at == LAST_SEEN_AT

    require_token.assert_called_once_with(FAILOVER_TOKEN)
    list_cameras.assert_awaited_once_with(DB)


@pytest.mark.asyncio
async def test_failover_cameras_rejects_invalid_token_without_listing_cameras():
    error = HTTPException(
        status_code=401,
        detail="Invalid failover controller token",
    )

    with (
        patch(
            "app.api.controllers.internal_failover.require_failover_controller_token",
            side_effect=error,
        ) as require_token,
        patch(
            "app.api.controllers.internal_failover.list_failover_cameras",
            new=AsyncMock(),
        ) as list_cameras,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await failover_cameras(
                db=DB,
                x_failover_token="wrong-token",
            )

    assert exc_info.value is error
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid failover controller token"

    require_token.assert_called_once_with("wrong-token")
    list_cameras.assert_not_awaited()


@pytest.mark.asyncio
async def test_failover_cameras_rejects_missing_token_without_listing_cameras():
    error = HTTPException(
        status_code=401,
        detail="Invalid failover controller token",
    )

    with (
        patch(
            "app.api.controllers.internal_failover.require_failover_controller_token",
            side_effect=error,
        ) as require_token,
        patch(
            "app.api.controllers.internal_failover.list_failover_cameras",
            new=AsyncMock(),
        ) as list_cameras,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await failover_cameras(
                db=DB,
                x_failover_token=None,
            )

    assert exc_info.value is error
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid failover controller token"

    require_token.assert_called_once_with(None)
    list_cameras.assert_not_awaited()


@pytest.mark.asyncio
async def test_failover_cameras_propagates_camera_listing_error():
    error = RuntimeError("Unable to retrieve failover cameras")

    with (
        patch(
            "app.api.controllers.internal_failover.require_failover_controller_token",
            return_value=None,
        ) as require_token,
        patch(
            "app.api.controllers.internal_failover.list_failover_cameras",
            new=AsyncMock(side_effect=error),
        ) as list_cameras,
    ):
        with pytest.raises(RuntimeError, match="Unable to retrieve failover cameras"):
            await failover_cameras(
                db=DB,
                x_failover_token=FAILOVER_TOKEN,
            )

    require_token.assert_called_once_with(FAILOVER_TOKEN)
    list_cameras.assert_awaited_once_with(DB)


@pytest.mark.asyncio
async def test_failover_cameras_returns_empty_data_when_no_cameras_exist():
    expected_response = FailoverCamerasRes(data=[])

    with (
        patch(
            "app.api.controllers.internal_failover.require_failover_controller_token",
            return_value=None,
        ) as require_token,
        patch(
            "app.api.controllers.internal_failover.list_failover_cameras",
            new=AsyncMock(return_value=expected_response),
        ) as list_cameras,
    ):
        response = await failover_cameras(
            db=DB,
            x_failover_token=FAILOVER_TOKEN,
        )

    assert isinstance(response, FailoverCamerasRes)
    assert response.data == []

    require_token.assert_called_once_with(FAILOVER_TOKEN)
    list_cameras.assert_awaited_once_with(DB)