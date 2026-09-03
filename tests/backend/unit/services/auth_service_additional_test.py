from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.services import auth_service as service


TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Password123!"


def make_db():
    db = Mock()
    db.add = Mock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


class TestRegisterUserAdditional:
    @pytest.mark.asyncio
    async def test_supports_lowercase_cognito_response_keys(self):
        db = make_db()
        db.flush.side_effect = lambda: None
        user_id = "11111111-1111-1111-1111-111111111111"

        def add(user):
            user.id = user_id

        db.add.side_effect = add

        with (
            patch.object(
                service,
                "sign_up",
                return_value={"user_sub": "lower-sub", "user_confirmed": True},
            ),
            patch.object(service, "create_audit_log_item"),
        ):
            result = await service.register_user(
                {
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "firstName": "Test",
                    "lastName": "User",
                    "address": "JHB",
                },
                db,
            )

        assert result == {
            "success": True,
            "data": {"user_sub": "lower-sub", "user_confirmed": True},
        }
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rolls_back_when_local_user_persistence_fails(self):
        db = make_db()
        db.flush.side_effect = RuntimeError("database unavailable")

        with patch.object(
            service,
            "sign_up",
            return_value={"UserSub": "cognito-sub", "UserConfirmed": False},
        ):
            with pytest.raises(RuntimeError, match="database unavailable"):
                await service.register_user(
                    {
                        "email": TEST_EMAIL,
                        "password": TEST_PASSWORD,
                        "firstName": "Test",
                        "lastName": "User",
                        "address": "JHB",
                    },
                    db,
                )

        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()


class TestAuthenticateUserAdditional:
    @pytest.mark.asyncio
    async def test_unknown_challenge_response_becomes_authentication_error(self):
        with patch.object(
            service,
            "login",
            return_value={
                "challenge": "SMS_MFA",
                "session": "session",
            },
        ):
            with pytest.raises(HTTPException) as exc:
                await service.authenticate_user(
                    {"email": TEST_EMAIL, "password": TEST_PASSWORD}
                )

        assert exc.value.status_code == 400
        assert exc.value.detail["error"] == "AuthenticationFailed"

    @pytest.mark.asyncio
    async def test_empty_cognito_response_becomes_authentication_error(self):
        with patch.object(service, "login", return_value={}):
            with pytest.raises(HTTPException) as exc:
                await service.authenticate_user(
                    {"email": TEST_EMAIL, "password": TEST_PASSWORD}
                )

        assert exc.value.status_code == 400
        assert exc.value.detail == {
            "error": "AuthenticationFailed",
            "message": {},
        }


class TestResendConfirmationCodeAdditional:
    @pytest.mark.asyncio
    async def test_uses_default_message_when_cognito_message_is_missing(self):
        with patch.object(service, "resend_code", return_value={}):
            result = await service.resend_confirmation_code({"email": TEST_EMAIL})

        assert result == {
            "success": True,
            "data": {"message": "sent"},
        }


class TestCompleteMfaAdditional:
    @pytest.mark.asyncio
    async def test_optional_refresh_token_is_allowed_to_be_missing(self):
        with patch.object(
            service,
            "respond_to_mfa",
            return_value={
                "access_token": "access",
                "id_token": "identity",
                "expires_in": 900,
                "token_type": "Bearer",
            },
        ):
            result = await service.complete_mfa(
                {
                    "email": TEST_EMAIL,
                    "session": "session",
                    "code": "123456",
                }
            )

        assert result["success"] is True
        assert result["data"] == {
            "access_token": "access",
            "id_token": "identity",
            "refresh_token": None,
            "token_type": "Bearer",
            "expires_in": 900,
        }