from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.pairing_token import (
    get_pairing_token,
    pair_agent,
)
from app.models.camera import CameraVisibilityEnum
from app.schemas.camera import CameraRes
from app.schemas.pairing_token import (
    EdgeAgentsCredentialsRes,
    EdgeAgentsCredentialsSchema,
    LinkPropertyToken,
    LinkPropertyTokenRes,
)
from starlette.requests import Request


PROPERTY_ID = uuid4()
CAMERA_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()
REQUEST = Request(
    {
        "type": "http",
        "method": "GET",
        "path": "/pairing-token/test",
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
    }
)
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
EXPIRES_AT = datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc)


def make_pairing_token_response():
    return LinkPropertyTokenRes(
        status=200,
        message="Pairing token generated successfully",
        data=LinkPropertyToken(
            token="ABC-DEF-GHI",
            expires_at=EXPIRES_AT,
        ),
    )


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


def make_pair_agent_response():
    return EdgeAgentsCredentialsRes(
        status=201,
        message="Agent paired successfully",
        data=EdgeAgentsCredentialsSchema(
            property_id=PROPERTY_ID,
            address="123 Test Street",
            api_key="wd_test-api-key",
            cameras=[make_camera_response()],
            created_at=CREATED_AT,
        ),
    )


@pytest.mark.asyncio
async def test_get_pairing_token_delegates_to_service():
    expected = make_pairing_token_response()

    with patch(
        "app.api.controllers.pairing_token.get_pairing_token_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_pairing_token(
            REQUEST,
            PROPERTY_ID,
            DB,
            CLAIMS,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        PROPERTY_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_pairing_token_propagates_service_error():
    error = HTTPException(
        status_code=403,
        detail="Insufficient permissions to generate a pairing token",
    )

    with patch(
        "app.api.controllers.pairing_token.get_pairing_token_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_pairing_token(
                REQUEST,
                PROPERTY_ID,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        PROPERTY_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_pair_agent_delegates_to_service():
    expected = make_pair_agent_response()

    with patch(
        "app.api.controllers.pairing_token.pair_agent_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await pair_agent(
            REQUEST,
            "ABC-DEF-GHI",
            DB,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        "ABC-DEF-GHI",
        DB,
    )


@pytest.mark.asyncio
async def test_pair_agent_propagates_service_error():
    error = HTTPException(
        status_code=400,
        detail="Token is expired or invalid",
    )

    with patch(
        "app.api.controllers.pairing_token.pair_agent_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await pair_agent(
                REQUEST,
                "INVALID-TOKEN",
                DB,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        "INVALID-TOKEN",
        DB,
    )