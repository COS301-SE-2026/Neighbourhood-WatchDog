from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.api.controllers.auth import (
    auth_ping,
    confirm,
    get_current_user_info,
    login,
    resend_code,
    signup,
    verify_mfa,
)
from app.schemas.auth import (
    ConfirmSignUpRequest,
    LoginRequest,
    ResendCodeRequest,
    SignUpRequest,
    VerifyMFARequest,
)


REQUEST = Mock()
DB = Mock()

SIGNUP_PAYLOAD = SignUpRequest(
    email="zaman@example.com",
    password="Password123!",
    firstName="Zaman",
    lastName="Bassa",
    address="Pretoria, South Africa",
)

LOGIN_PAYLOAD = LoginRequest(
    email="zaman@example.com",
    password="Password123!",
)

CONFIRM_PAYLOAD = ConfirmSignUpRequest(
    email="zaman@example.com",
    code="123456",
)

RESEND_PAYLOAD = ResendCodeRequest(
    email="zaman@example.com",
)

MFA_PAYLOAD = VerifyMFARequest(
    email="zaman@example.com",
    session="mfa-session",
    code="123456",
)


def test_auth_ping_returns_health_check_response():
    response = auth_ping()

    assert response == {
        "status": "ok",
        "message": "auth router is ALIVE",
    }


@pytest.mark.asyncio
async def test_signup_converts_payload_and_delegates_to_register_user():
    expected_response = {
        "success": True,
        "data": {
            "user_sub": "cognito-user-sub",
            "user_confirmed": False,
        },
    }

    with patch(
        "app.api.controllers.auth.register_user",
        new=AsyncMock(return_value=expected_response),
    ) as register_user:
        response = await signup(
            REQUEST,
            SIGNUP_PAYLOAD,
            DB,
        )

    assert response == expected_response

    register_user.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "password": "Password123!",
            "firstName": "Zaman",
            "lastName": "Bassa",
            "address": "Pretoria, South Africa",
        },
        DB,
    )


@pytest.mark.asyncio
async def test_signup_propagates_service_error():
    error = HTTPException(
        status_code=409,
        detail="User already exists",
    )

    with patch(
        "app.api.controllers.auth.register_user",
        new=AsyncMock(side_effect=error),
    ) as register_user:
        with pytest.raises(HTTPException) as exc_info:
            await signup(
                REQUEST,
                SIGNUP_PAYLOAD,
                DB,
            )

    assert exc_info.value is error

    register_user.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "password": "Password123!",
            "firstName": "Zaman",
            "lastName": "Bassa",
            "address": "Pretoria, South Africa",
        },
        DB,
    )


@pytest.mark.asyncio
async def test_login_converts_payload_and_delegates_to_authenticate_user():
    expected_response = {
        "success": True,
        "data": {
            "mfa_required": True,
            "session": "mfa-session",
            "delivery": {
                "medium": "EMAIL",
                "destination": "z***@e***",
            },
        },
    }

    with patch(
        "app.api.controllers.auth.authenticate_user",
        new=AsyncMock(return_value=expected_response),
    ) as authenticate_user:
        response = await login(
            REQUEST,
            LOGIN_PAYLOAD,
        )

    assert response == expected_response

    authenticate_user.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "password": "Password123!",
        }
    )


@pytest.mark.asyncio
async def test_login_propagates_authentication_error():
    error = HTTPException(
        status_code=401,
        detail="Invalid credentials",
    )

    with patch(
        "app.api.controllers.auth.authenticate_user",
        new=AsyncMock(side_effect=error),
    ) as authenticate_user:
        with pytest.raises(HTTPException) as exc_info:
            await login(
                REQUEST,
                LOGIN_PAYLOAD,
            )

    assert exc_info.value is error

    authenticate_user.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "password": "Password123!",
        }
    )


@pytest.mark.asyncio
async def test_confirm_converts_payload_and_delegates_to_confirm_user():
    expected_response = {
        "success": True,
        "data": {
            "confirmed": True,
        },
    }

    with patch(
        "app.api.controllers.auth.confirm_user",
        new=AsyncMock(return_value=expected_response),
    ) as confirm_user:
        response = await confirm(
            REQUEST,
            CONFIRM_PAYLOAD,
        )

    assert response == expected_response

    confirm_user.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "code": "123456",
        }
    )


@pytest.mark.asyncio
async def test_confirm_propagates_confirmation_error():
    error = HTTPException(
        status_code=400,
        detail="Invalid confirmation code",
    )

    with patch(
        "app.api.controllers.auth.confirm_user",
        new=AsyncMock(side_effect=error),
    ) as confirm_user:
        with pytest.raises(HTTPException) as exc_info:
            await confirm(
                REQUEST,
                CONFIRM_PAYLOAD,
            )

    assert exc_info.value is error

    confirm_user.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "code": "123456",
        }
    )


@pytest.mark.asyncio
async def test_resend_code_converts_payload_and_delegates_to_resend_confirmation_code():
    expected_response = {
        "success": True,
        "data": {
            "message": "Confirmation code sent",
        },
    }

    with patch(
        "app.api.controllers.auth.resend_confirmation_code",
        new=AsyncMock(return_value=expected_response),
    ) as resend_confirmation_code:
        response = await resend_code(
            REQUEST,
            RESEND_PAYLOAD,
        )

    assert response == expected_response

    resend_confirmation_code.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
        }
    )


@pytest.mark.asyncio
async def test_resend_code_propagates_service_error():
    error = HTTPException(
        status_code=404,
        detail="User not found",
    )

    with patch(
        "app.api.controllers.auth.resend_confirmation_code",
        new=AsyncMock(side_effect=error),
    ) as resend_confirmation_code:
        with pytest.raises(HTTPException) as exc_info:
            await resend_code(
                REQUEST,
                RESEND_PAYLOAD,
            )

    assert exc_info.value is error

    resend_confirmation_code.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
        }
    )


@pytest.mark.asyncio
async def test_verify_mfa_converts_payload_and_delegates_to_complete_mfa():
    expected_response = {
        "success": True,
        "data": {
            "access_token": "access-token",
            "id_token": "id-token",
            "refresh_token": "refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    }

    with patch(
        "app.api.controllers.auth.complete_mfa",
        new=AsyncMock(return_value=expected_response),
    ) as complete_mfa:
        response = await verify_mfa(
            REQUEST,
            MFA_PAYLOAD,
        )

    assert response == expected_response

    complete_mfa.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "session": "mfa-session",
            "code": "123456",
        }
    )


@pytest.mark.asyncio
async def test_verify_mfa_propagates_service_error():
    error = HTTPException(
        status_code=401,
        detail="Authentication failed",
    )

    with patch(
        "app.api.controllers.auth.complete_mfa",
        new=AsyncMock(side_effect=error),
    ) as complete_mfa:
        with pytest.raises(HTTPException) as exc_info:
            await verify_mfa(
                REQUEST,
                MFA_PAYLOAD,
            )

    assert exc_info.value is error

    complete_mfa.assert_awaited_once_with(
        {
            "email": "zaman@example.com",
            "session": "mfa-session",
            "code": "123456",
        }
    )


@pytest.mark.asyncio
async def test_get_current_user_info_rejects_missing_cognito_subject():
    current_user = {
        "email": "zaman@example.com",
    }

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_info(
            REQUEST,
            DB,
            current_user,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token claims"


@pytest.mark.asyncio
async def test_get_current_user_info_rejects_unknown_database_user():
    current_user = {
        "sub": "cognito-user-sub",
        "given_name": "Zaman",
        "family_name": "Bassa",
    }

    result = Mock()
    result.scalar_one_or_none.return_value = None

    db = Mock()
    db.execute = AsyncMock(return_value=result)

    with patch(
        "app.api.controllers.auth.create_user",
        new=AsyncMock(),
    ) as create_user:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_info(
                REQUEST,
                db,
                current_user,
            )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"

    db.execute.assert_awaited_once()
    create_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_info_finds_user_and_refreshes_user_data():
    current_user = {
        "sub": "cognito-user-sub",
        "given_name": "Zaman",
        "family_name": "Bassa",
    }

    database_user = Mock()
    database_user.email = "zaman@example.com"

    result = Mock()
    result.scalar_one_or_none.return_value = database_user

    db = Mock()
    db.execute = AsyncMock(return_value=result)

    expected_response = {
        "id": "database-user-id",
        "email": "zaman@example.com",
        "first_name": "Zaman",
        "last_name": "Bassa",
    }

    with patch(
        "app.api.controllers.auth.create_user",
        new=AsyncMock(return_value=expected_response),
    ) as create_user:
        response = await get_current_user_info(
            REQUEST,
            db,
            current_user,
        )

    assert response == expected_response

    db.execute.assert_awaited_once()

    create_user.assert_awaited_once_with(
        email="zaman@example.com",
        first_name="Zaman",
        last_name="Bassa",
        cognito_sub="cognito-user-sub",
        db=db,
    )


@pytest.mark.asyncio
async def test_get_current_user_info_uses_empty_names_when_claims_are_missing():
    current_user = {
        "sub": "cognito-user-sub",
    }

    database_user = Mock()
    database_user.email = "zaman@example.com"

    result = Mock()
    result.scalar_one_or_none.return_value = database_user

    db = Mock()
    db.execute = AsyncMock(return_value=result)

    expected_response = {
        "id": "database-user-id",
        "email": "zaman@example.com",
    }

    with patch(
        "app.api.controllers.auth.create_user",
        new=AsyncMock(return_value=expected_response),
    ) as create_user:
        response = await get_current_user_info(
            REQUEST,
            db,
            current_user,
        )

    assert response == expected_response

    create_user.assert_awaited_once_with(
        email="zaman@example.com",
        first_name="",
        last_name="",
        cognito_sub="cognito-user-sub",
        db=db,
    )


@pytest.mark.asyncio
async def test_get_current_user_info_propagates_create_user_error():
    current_user = {
        "sub": "cognito-user-sub",
        "given_name": "Zaman",
        "family_name": "Bassa",
    }

    database_user = Mock()
    database_user.email = "zaman@example.com"

    result = Mock()
    result.scalar_one_or_none.return_value = database_user

    db = Mock()
    db.execute = AsyncMock(return_value=result)

    error = HTTPException(
        status_code=500,
        detail="Failed to create user",
    )

    with patch(
        "app.api.controllers.auth.create_user",
        new=AsyncMock(side_effect=error),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_info(
                REQUEST,
                db,
                current_user,
            )

    assert exc_info.value is error