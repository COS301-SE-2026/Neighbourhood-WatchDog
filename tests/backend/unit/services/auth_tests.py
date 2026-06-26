import pytest
from unittest.mock import MagicMock
import backend.app.services.auth_service as auth_service
from backend.app.services.auth_service import authenticate_user, register_user, confirm_user, resend_confirmation_code


#THIS IS THE MOCK AWS COGNITO # we do not want to make calls to AWS... we know they work :)
@pytest.fixture(autouse=True)
def mock_cognito(monkeypatch):

    monkeypatch.setattr(auth_service, "sign_up", MagicMock(return_value={
        "UserSub": "abc-123",
        "UserConfirmed": False
    }))

    monkeypatch.setattr(auth_service, "login", MagicMock(return_value={
        "access_token": "token",
        "id_token": "id",
        "refresh_token": "refresh",
        "expires_in": 3600,
        "token_type": "Bearer"
    }))

    monkeypatch.setattr(auth_service, "confirm_sign_up", MagicMock(return_value={
        "status": "CONFIRMED"
    }))

    monkeypatch.setattr(auth_service, "resend_code", MagicMock(return_value={
        "message": "sent"
    }))

#START TESTS
#SIGNUP
def test_register_user_success(mock_cognito):
    payload = {
        "email": "test@example.com",
        "password": "Password123!",
        "name": "Zaman",
        "address": "JHB"
    }

    result = auth_service.register_user(payload)

    assert result["success"] is True # DID IT SUCCESFULLY EXECUTE
    assert result["data"]["user_sub"] == "abc-123"

#LOGIN
def test_login_success(mock_cognito):
    result = auth_service.authenticate_user({
        "email": "email@example.com",
        "password": "Password123!"
    })

    assert result["success"] is True
    assert result["data"]["access_token"] == "token"
    assert result["data"]["expires_in"] == 3600

#CONFIRM
def test_confirm_user_success(mock_cognito):
    result = auth_service.confirm_user({
        "email": "test@example.com",
        "code": "123456"
    })

    assert result["success"] is True
    assert result["data"]["status"] == "CONFIRMED"

#RESEND
def test_resend_code_success(mock_cognito):
    result = auth_service.resend_confirmation_code({
        "email": "test@example.com"
    })

    assert result["success"] is True

#TODO: end to end testing 