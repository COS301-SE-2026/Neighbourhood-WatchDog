from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.camera import (
    deregister_camera,
    edit_camera,
    get_property_cameras,
    register_camera,
)
from app.models.camera import CameraVisibilityEnum
from app.schemas.camera import (
    CameraEditReq,
    CameraListItemRes,
    CameraRes,
    CamerasRes,
    EditCameraRes,
    RegisterCameraReq,
    RegisterCameraRes,
)


PROPERTY_ID = uuid4()
CAMERA_ID = uuid4()
CLAIMS = {"sub": "cognito-sub-123"}
DB = Mock()
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_camera_response():
    return CameraRes(
        id=CAMERA_ID,
        property_id=PROPERTY_ID,
        neighbourhood_id=None,
        name="Front Camera",
        visibility=CameraVisibilityEnum.PRIVATE,
        location="Front gate",
        rtsp_url="rtsp://example.test/front",
        enabled=True,
        created_at=CREATED_AT,
    )


def make_camera_list_item():
    return CameraListItemRes(
        id=CAMERA_ID,
        property_id=PROPERTY_ID,
        neighbourhood_id=None,
        name="Front Camera",
        visibility=CameraVisibilityEnum.PRIVATE,
        location="Front gate",
        enabled=True,
        created_at=CREATED_AT,
        edge_agent_available=True,
    )


@pytest.mark.asyncio
async def test_register_camera_checks_property_admin_and_delegates():
    request = RegisterCameraReq(
        name="Front Camera",
        rtsp_url="rtsp://example.test/front",
        location="Front gate",
        visibility=CameraVisibilityEnum.PRIVATE,
        property_id=PROPERTY_ID,
    )
    expected_camera = make_camera_response()

    with patch(
        "app.api.controllers.camera.is_property_admin",
        new=AsyncMock(return_value=True),
    ) as is_admin, patch(
        "app.api.controllers.camera.register_camera_handler",
        new=AsyncMock(return_value=expected_camera),
    ) as handler:
        response = await register_camera(request, DB, CLAIMS)

    assert isinstance(response, RegisterCameraRes)
    assert response.status == 201
    assert response.message == "Camera Created Successfully"
    assert response.data == expected_camera

    is_admin.assert_awaited_once_with(PROPERTY_ID, CLAIMS, DB)
    handler.assert_awaited_once_with(request, DB, CLAIMS)


@pytest.mark.asyncio
async def test_register_camera_rejects_non_property_admin():
    request = RegisterCameraReq(
        name="Front Camera",
        rtsp_url="rtsp://example.test/front",
        location="Front gate",
        visibility=CameraVisibilityEnum.PRIVATE,
        property_id=PROPERTY_ID,
    )

    with patch(
        "app.api.controllers.camera.is_property_admin",
        new=AsyncMock(return_value=False),
    ) as is_admin, patch(
        "app.api.controllers.camera.register_camera_handler",
        new=AsyncMock(),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await register_camera(request, DB, CLAIMS)

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "You do not have permission to add a camera to this property"
    )
    is_admin.assert_awaited_once_with(PROPERTY_ID, CLAIMS, DB)
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_camera_propagates_service_error():
    request = RegisterCameraReq(
        name="Front Camera",
        rtsp_url="rtsp://example.test/front",
        location="Front gate",
        visibility=CameraVisibilityEnum.PRIVATE,
        property_id=PROPERTY_ID,
    )
    error = HTTPException(status_code=404, detail="Property not found")

    with patch(
        "app.api.controllers.camera.is_property_admin",
        new=AsyncMock(return_value=True),
    ), patch(
        "app.api.controllers.camera.register_camera_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await register_camera(request, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(request, DB, CLAIMS)


@pytest.mark.asyncio
async def test_deregister_camera_delegates_to_service():
    with patch(
        "app.api.controllers.camera.deregister_camera_handler",
        new=AsyncMock(return_value=None),
    ) as handler:
        response = await deregister_camera(CAMERA_ID, DB, CLAIMS)

    assert response is None
    handler.assert_awaited_once_with(CAMERA_ID, DB, CLAIMS)


@pytest.mark.asyncio
async def test_deregister_camera_propagates_service_error():
    error = HTTPException(status_code=404, detail="Camera not found")

    with patch(
        "app.api.controllers.camera.deregister_camera_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await deregister_camera(CAMERA_ID, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(CAMERA_ID, DB, CLAIMS)


@pytest.mark.asyncio
async def test_get_property_cameras_returns_cached_value():
    property_id = str(PROPERTY_ID)
    expected = CamerasRes(
        status=200,
        data=[make_camera_list_item()],
    )

    with patch(
        "app.api.controllers.camera.camera_property_cache_key",
        return_value="camera-cache-key",
    ) as cache_key, patch(
        "app.api.controllers.camera.cache_get_or_set",
        new=AsyncMock(return_value=expected.model_dump(mode="json")),
    ) as cache, patch(
        "app.api.controllers.camera.list_cameras_handler",
        new=AsyncMock(),
    ) as handler:
        response = await get_property_cameras(property_id, DB, CLAIMS)

    assert response == expected.model_dump(mode="json")
    cache_key.assert_called_once_with(property_id)
    cache.assert_awaited_once()
    assert cache.await_args.args[0] == "camera-cache-key"
    assert cache.await_args.args[1] == 30
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_property_cameras_fetches_and_caches_on_cache_miss():
    property_id = str(PROPERTY_ID)
    expected = CamerasRes(
        status=200,
        data=[make_camera_list_item()],
    )

    async def execute_fetch(_key, _ttl, fetch):
        return await fetch()

    with patch(
        "app.api.controllers.camera.camera_property_cache_key",
        return_value="camera-cache-key",
    ), patch(
        "app.api.controllers.camera.cache_get_or_set",
        new=AsyncMock(side_effect=execute_fetch),
    ), patch(
        "app.api.controllers.camera.list_cameras_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_property_cameras(property_id, DB, CLAIMS)

    assert response == expected.model_dump(mode="json")
    handler.assert_awaited_once_with(property_id, DB, CLAIMS)


@pytest.mark.asyncio
async def test_get_property_cameras_propagates_service_error():
    property_id = str(PROPERTY_ID)
    error = HTTPException(status_code=403, detail="Property access denied")

    async def execute_fetch(_key, _ttl, fetch):
        return await fetch()

    with patch(
        "app.api.controllers.camera.cache_get_or_set",
        new=AsyncMock(side_effect=execute_fetch),
    ), patch(
        "app.api.controllers.camera.list_cameras_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_property_cameras(property_id, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(property_id, DB, CLAIMS)


@pytest.mark.asyncio
async def test_edit_camera_delegates_and_wraps_response():
    request = CameraEditReq(
        name="Updated Camera",
        location="Updated location",
        visibility=CameraVisibilityEnum.RESTRICTED,
        enabled=False,
    )
    updated_camera = make_camera_response()

    with patch(
        "app.api.controllers.camera.edit_camera_handler",
        new=AsyncMock(return_value=updated_camera),
    ) as handler:
        response = await edit_camera(CAMERA_ID, request, DB, CLAIMS)

    assert isinstance(response, EditCameraRes)
    assert response.status == 200
    assert response.message == "Camera updated successfully"
    assert response.data == updated_camera
    handler.assert_awaited_once_with(CAMERA_ID, request, DB, CLAIMS)


@pytest.mark.asyncio
async def test_edit_camera_propagates_service_error():
    request = CameraEditReq(name="Updated Camera")
    error = HTTPException(status_code=404, detail="Camera not found")

    with patch(
        "app.api.controllers.camera.edit_camera_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await edit_camera(CAMERA_ID, request, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(CAMERA_ID, request, DB, CLAIMS)