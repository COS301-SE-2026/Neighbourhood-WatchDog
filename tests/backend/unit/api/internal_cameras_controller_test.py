from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Response

from app.api.controllers.internal_cameras import (
    CAMERAS_ENABLED_TTL,
    authorize_mediamtx,
    list_enabled_cameras,
)
from app.schemas.camera import (
    EnabledCamerasRes,
    ListEnabledCameras,
    MediaMtxAuthRequest,
)


PROPERTY_ID = uuid4()
CAMERA_ID = uuid4()
DB = Mock()
CREDENTIAL = Mock(property_id=PROPERTY_ID)


def make_enabled_camera():
    return EnabledCamerasRes(
        id=CAMERA_ID,
        rtsp_url="rtsp://safe-camera-url",
        enabled=True,
        neighbourhood_id=uuid4(),
        confidence_threshold=0.75,
        zones=[
            [
                [0.1, 0.1],
                [0.9, 0.1],
                [0.9, 0.9],
                [0.1, 0.9],
            ]
        ],
        publish_username="camera-user",
        publish_password="camera-password",
    )


def make_enabled_cameras_response():
    return ListEnabledCameras(
        data=[make_enabled_camera()],
    )


@pytest.mark.asyncio
async def test_list_enabled_cameras_records_heartbeat_fetches_cameras_and_uses_cache():
    expected_response = make_enabled_cameras_response()
    expected_cached_value = expected_response.model_dump(mode="json")

    heartbeat = AsyncMock()
    list_cameras_handler = AsyncMock(return_value=expected_response)

    async def execute_fetch(key, ttl_seconds, fetch_fn):
        assert key == (
            f"cache:camera:internal:property_id:{PROPERTY_ID}"
        )
        assert ttl_seconds == CAMERAS_ENABLED_TTL
        return await fetch_fn()

    with (
        patch(
            "app.api.controllers.internal_cameras.record_edge_agent_heartbeat",
            new=heartbeat,
        ),
        patch(
            "app.api.controllers.internal_cameras.list_enabled_cameras_for_agent_handler",
            new=list_cameras_handler,
        ) as list_cameras,
        patch(
            "app.api.controllers.internal_cameras.cache_get_or_set",
            new=AsyncMock(side_effect=execute_fetch),
        ) as cache_get_or_set,
    ):
        response = await list_enabled_cameras(
            db=DB,
            credential=CREDENTIAL,
        )

    assert response == expected_cached_value

    heartbeat.assert_awaited_once_with(
        credential=CREDENTIAL,
        db=DB,
    )

    list_cameras.assert_awaited_once_with(
        property_id=PROPERTY_ID,
        db=DB,
    )

    cache_get_or_set.assert_awaited_once()
    cache_args = cache_get_or_set.await_args.args
    assert cache_args[0] == (
        f"cache:camera:internal:property_id:{PROPERTY_ID}"
    )
    assert cache_args[1] == CAMERAS_ENABLED_TTL
    assert callable(cache_args[2])


@pytest.mark.asyncio
async def test_list_enabled_cameras_returns_cached_value_without_fetching_cameras():
    cached_value = {
        "data": [
            {
                "id": str(CAMERA_ID),
                "rtsp_url": "rtsp://cached-camera-url",
                "enabled": True,
                "neighbourhood_id": None,
                "confidence_threshold": 0.8,
                "zones": [],
                "publish_username": "cached-user",
                "publish_password": "cached-password",
            }
        ]
    }

    heartbeat = AsyncMock()

    with (
        patch(
            "app.api.controllers.internal_cameras.record_edge_agent_heartbeat",
            new=heartbeat,
        ),
        patch(
            "app.api.controllers.internal_cameras.list_enabled_cameras_for_agent_handler",
            new=AsyncMock(),
        ) as list_cameras,
        patch(
            "app.api.controllers.internal_cameras.cache_get_or_set",
            new=AsyncMock(return_value=cached_value),
        ) as cache_get_or_set,
    ):
        response = await list_enabled_cameras(
            db=DB,
            credential=CREDENTIAL,
        )

    assert response == cached_value

    heartbeat.assert_awaited_once_with(
        credential=CREDENTIAL,
        db=DB,
    )

    list_cameras.assert_not_awaited()

    cache_get_or_set.assert_awaited_once()
    cache_args = cache_get_or_set.await_args.args
    assert cache_args[0] == (
        f"cache:camera:internal:property_id:{PROPERTY_ID}"
    )
    assert cache_args[1] == CAMERAS_ENABLED_TTL
    assert callable(cache_args[2])


@pytest.mark.asyncio
async def test_list_enabled_cameras_propagates_heartbeat_error():
    error = HTTPException(
        status_code=401,
        detail="Invalid or missing edge agent credentials",
    )

    with (
        patch(
            "app.api.controllers.internal_cameras.record_edge_agent_heartbeat",
            new=AsyncMock(side_effect=error),
        ) as heartbeat,
        patch(
            "app.api.controllers.internal_cameras.cache_get_or_set",
            new=AsyncMock(),
        ) as cache_get_or_set,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await list_enabled_cameras(
                db=DB,
                credential=CREDENTIAL,
            )

    assert exc_info.value is error

    heartbeat.assert_awaited_once_with(
        credential=CREDENTIAL,
        db=DB,
    )

    cache_get_or_set.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_enabled_cameras_propagates_camera_service_error():
    error = HTTPException(
        status_code=500,
        detail="Failed to retrieve enabled cameras",
    )

    heartbeat = AsyncMock()

    async def execute_fetch(key, ttl_seconds, fetch_fn):
        return await fetch_fn()

    with (
        patch(
            "app.api.controllers.internal_cameras.record_edge_agent_heartbeat",
            new=heartbeat,
        ),
        patch(
            "app.api.controllers.internal_cameras.list_enabled_cameras_for_agent_handler",
            new=AsyncMock(side_effect=error),
        ) as list_cameras,
        patch(
            "app.api.controllers.internal_cameras.cache_get_or_set",
            new=AsyncMock(side_effect=execute_fetch),
        ) as cache_get_or_set,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await list_enabled_cameras(
                db=DB,
                credential=CREDENTIAL,
            )

    assert exc_info.value is error

    heartbeat.assert_awaited_once_with(
        credential=CREDENTIAL,
        db=DB,
    )

    list_cameras.assert_awaited_once_with(
        property_id=PROPERTY_ID,
        db=DB,
    )

    cache_get_or_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_authorize_mediamtx_delegates_request_and_database_session():
    request = MediaMtxAuthRequest(
        user="camera-user",
        password="camera-password",
        action="publish",
        path=f"cameras/{CAMERA_ID}",
        protocol="rtsp",
        ip="127.0.0.1",
        id="media-session-id",
        query="",
    )
    expected_response = Response(status_code=204)

    with patch(
        "app.api.controllers.internal_cameras.authorize_mediamtx_for_agent_handler",
        new=AsyncMock(return_value=expected_response),
    ) as authorize_handler:
        response = await authorize_mediamtx(
            request=request,
            db=DB,
        )

    assert response is expected_response
    assert response.status_code == 204

    authorize_handler.assert_awaited_once_with(
        request=request,
        db=DB,
    )


@pytest.mark.asyncio
async def test_authorize_mediamtx_propagates_authorization_error():
    request = MediaMtxAuthRequest(
        user="wrong-user",
        password="wrong-password",
        action="publish",
        path=f"cameras/{CAMERA_ID}",
    )
    error = HTTPException(
        status_code=401,
        detail="Invalid publish credential for the requested camera path.",
    )

    with patch(
        "app.api.controllers.internal_cameras.authorize_mediamtx_for_agent_handler",
        new=AsyncMock(side_effect=error),
    ) as authorize_handler:
        with pytest.raises(HTTPException) as exc_info:
            await authorize_mediamtx(
                request=request,
                db=DB,
            )

    assert exc_info.value is error
    assert exc_info.value.status_code == 401

    authorize_handler.assert_awaited_once_with(
        request=request,
        db=DB,
    )


@pytest.mark.asyncio
async def test_authorize_mediamtx_propagates_forbidden_action_error():
    request = MediaMtxAuthRequest(
        user="camera-user",
        password="camera-password",
        action="unknown-action",
        path=f"cameras/{CAMERA_ID}",
    )
    error = HTTPException(
        status_code=403,
        detail="This MediaMTX action is not allowed.",
    )

    with patch(
        "app.api.controllers.internal_cameras.authorize_mediamtx_for_agent_handler",
        new=AsyncMock(side_effect=error),
    ) as authorize_handler:
        with pytest.raises(HTTPException) as exc_info:
            await authorize_mediamtx(
                request=request,
                db=DB,
            )

    assert exc_info.value is error
    assert exc_info.value.status_code == 403

    authorize_handler.assert_awaited_once_with(
        request=request,
        db=DB,
    )