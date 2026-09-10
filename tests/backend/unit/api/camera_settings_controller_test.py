from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.camera_settings import (
    create_zone,
    delete_zone,
    get_settings,
    update_settings,
)
from app.schemas.camera_settings import (
    CreateZoneRequest,
    UpdateCameraSettingsRequest,
)


CAMERA_ID = uuid4()
ZONE_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()


def make_settings_response():
    return {
        "camera_id": CAMERA_ID,
        "confidence_threshold": 0.75,
        "zones": [],
    }


def make_zone_response():
    return {
        "id": ZONE_ID,
        "camera_id": CAMERA_ID,
        "name": "Front Gate",
        "polygon": [
            [0.1, 0.1],
            [0.5, 0.1],
            [0.5, 0.5],
        ],
    }


@pytest.mark.asyncio
async def test_get_settings_delegates_to_service():
    expected = make_settings_response()

    with patch(
        "app.api.controllers.camera_settings.get_camera_settings_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_settings(CAMERA_ID, DB, CLAIMS)

    assert response is expected
    handler.assert_awaited_once_with(CAMERA_ID, DB, CLAIMS)


@pytest.mark.asyncio
async def test_get_settings_propagates_service_error():
    error = HTTPException(
        status_code=404,
        detail="Camera not found",
    )

    with patch(
        "app.api.controllers.camera_settings.get_camera_settings_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_settings(CAMERA_ID, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(CAMERA_ID, DB, CLAIMS)


@pytest.mark.asyncio
async def test_update_settings_delegates_threshold_to_service():
    payload = UpdateCameraSettingsRequest(
        confidence_threshold=0.8,
    )
    expected = {
        "camera_id": CAMERA_ID,
        "confidence_threshold": 0.8,
    }

    with patch(
        "app.api.controllers.camera_settings.update_camera_settings_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await update_settings(
            CAMERA_ID,
            payload,
            DB,
            CLAIMS,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        CAMERA_ID,
        0.8,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_update_settings_requires_confidence_threshold():
    payload = UpdateCameraSettingsRequest(
        confidence_threshold=None,
    )

    with patch(
        "app.api.controllers.camera_settings.update_camera_settings_handler",
        new=AsyncMock(),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await update_settings(
                CAMERA_ID,
                payload,
                DB,
                CLAIMS,
            )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "confidence_threshold is required"
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_settings_propagates_service_error():
    payload = UpdateCameraSettingsRequest(
        confidence_threshold=0.8,
    )
    error = HTTPException(
        status_code=404,
        detail="Camera not found",
    )

    with patch(
        "app.api.controllers.camera_settings.update_camera_settings_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await update_settings(
                CAMERA_ID,
                payload,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        CAMERA_ID,
        0.8,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_create_zone_maps_payload_fields_and_delegates():
    payload = CreateZoneRequest(
        name="Front Gate",
        polygon=[
            [0.1, 0.1],
            [0.5, 0.1],
            [0.5, 0.5],
        ],
    )
    expected = make_zone_response()

    with patch(
        "app.api.controllers.camera_settings.create_zone_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await create_zone(
            CAMERA_ID,
            payload,
            DB,
            CLAIMS,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        CAMERA_ID,
        payload.name,
        payload.polygon,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_create_zone_propagates_service_error():
    payload = CreateZoneRequest(
        name="Front Gate",
        polygon=[
            [0.1, 0.1],
            [0.5, 0.1],
            [0.5, 0.5],
        ],
    )
    error = HTTPException(
        status_code=404,
        detail="Camera not found",
    )

    with patch(
        "app.api.controllers.camera_settings.create_zone_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await create_zone(
                CAMERA_ID,
                payload,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        CAMERA_ID,
        payload.name,
        payload.polygon,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_delete_zone_delegates_to_service():
    with patch(
        "app.api.controllers.camera_settings.delete_zone_handler",
        new=AsyncMock(return_value=None),
    ) as handler:
        response = await delete_zone(
            CAMERA_ID,
            ZONE_ID,
            DB,
            CLAIMS,
        )

    assert response is None
    handler.assert_awaited_once_with(
        CAMERA_ID,
        ZONE_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_delete_zone_propagates_service_error():
    error = HTTPException(
        status_code=404,
        detail="Zone not found",
    )

    with patch(
        "app.api.controllers.camera_settings.delete_zone_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await delete_zone(
                CAMERA_ID,
                ZONE_ID,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        CAMERA_ID,
        ZONE_ID,
        DB,
        CLAIMS,
    )