from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.controllers.users import (
    get_my_context,
    get_my_settings,
    get_user_by_id,
    update_my_settings,
)
from app.models.neighbourhood_user import NeighbourhoodRole
from app.models.user import UserRole
from app.schemas.user import (
    CurrentUserContextRes,
    UpdateUserSettingsReq,
    UserSettingsResSchema,
)


USER_ID = uuid4()
CLAIMS = {"sub": "cognito-sub-123"}
DB = Mock()
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_user_response():
    return {
        "id": USER_ID,
        "email": "resident@example.com",
        "cognito_sub": "cognito-sub-123",
        "role": UserRole.RESIDENT,
        "created_at": CREATED_AT,
    }


def make_context():
    return CurrentUserContextRes(
        user={
            "id": USER_ID,
            "name": "Jane Doe",
            "system_role": UserRole.RESIDENT,
        },
        properties=[
            {
                "id": uuid4(),
                "address": "123 Test Street",
                "neighbourhood": {
                    "id": uuid4(),
                    "name": "Test Estate",
                    "role": NeighbourhoodRole.RESIDENT,
                },
                "is_admin": False,
            }
        ],
    )


def make_settings():
    return UserSettingsResSchema(
        first_name="Jane",
        last_name="Doe",
        email="resident@example.com",
        phone_number="+27820000000",
        system_role=UserRole.RESIDENT,
    )


@pytest.mark.asyncio
async def test_get_user_by_id_delegates_and_returns_service_result():
    expected = make_user_response()

    with patch(
        "app.api.controllers.users.get_user_by_id_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_user_by_id(USER_ID, DB, CLAIMS)

    assert response == expected
    handler.assert_awaited_once_with(USER_ID, DB, CLAIMS)


@pytest.mark.asyncio
async def test_get_user_by_id_propagates_not_found_error():
    error = HTTPException(status_code=404, detail="User not found")
    handler = AsyncMock(side_effect=error)

    with patch(
        "app.api.controllers.users.get_user_by_id_handler",
        new=handler,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_id(USER_ID, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(USER_ID, DB, CLAIMS)


@pytest.mark.asyncio
async def test_get_my_context_delegates_to_handler():
    expected = make_context()

    with patch(
        "app.api.controllers.users.get_current_user_context_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_my_context(CLAIMS, DB)

    assert response is expected
    handler.assert_awaited_once_with(CLAIMS, DB)


@pytest.mark.asyncio
async def test_get_my_context_propagates_authentication_error():
    error = HTTPException(status_code=401, detail="Invalid user")
    handler = AsyncMock(side_effect=error)

    with patch(
        "app.api.controllers.users.get_current_user_context_handler",
        new=handler,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_my_context(CLAIMS, DB)

    assert exc_info.value is error
    handler.assert_awaited_once_with(CLAIMS, DB)


@pytest.mark.asyncio
async def test_get_my_settings_returns_handler_result():
    expected = make_settings()

    with patch(
        "app.api.controllers.users.get_current_user_settings_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_my_settings(CLAIMS, DB)

    assert response == expected
    assert response.email == "resident@example.com"
    handler.assert_awaited_once_with(CLAIMS, DB)


@pytest.mark.asyncio
async def test_get_my_settings_propagates_missing_user_error():
    error = HTTPException(status_code=401, detail="User not found")
    handler = AsyncMock(side_effect=error)

    with patch(
        "app.api.controllers.users.get_current_user_settings_handler",
        new=handler,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_my_settings(CLAIMS, DB)

    assert exc_info.value is error
    handler.assert_awaited_once_with(CLAIMS, DB)


@pytest.mark.asyncio
async def test_update_my_settings_delegates_data_claims_and_db():
    payload = UpdateUserSettingsReq(
        first_name="Jane",
        last_name="Doe",
        phone_number="+27820000000",
    )
    expected = make_settings()

    with patch(
        "app.api.controllers.users.update_current_user_settings_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await update_my_settings(payload, CLAIMS, DB)

    assert response is expected
    handler.assert_awaited_once_with(payload, CLAIMS, DB)


@pytest.mark.asyncio
async def test_update_my_settings_propagates_validation_error_from_service():
    payload = UpdateUserSettingsReq(
        first_name="Jane",
        last_name="Doe",
    )
    error = HTTPException(status_code=400, detail="Invalid first name")
    handler = AsyncMock(side_effect=error)

    with patch(
        "app.api.controllers.users.update_current_user_settings_handler",
        new=handler,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await update_my_settings(payload, CLAIMS, DB)

    assert exc_info.value is error
    handler.assert_awaited_once_with(payload, CLAIMS, DB)


def test_update_user_settings_request_requires_names():
    with pytest.raises(ValidationError):
        UpdateUserSettingsReq(first_name="Jane")

    with pytest.raises(ValidationError):
        UpdateUserSettingsReq(last_name="Doe")