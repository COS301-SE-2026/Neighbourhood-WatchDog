import pytest
from unittest.mock import MagicMock , patch
import backend.app.services.auth_service as auth_service



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
        "token_type": "Bearer",
    }))

    monkeypatch.setattr(auth_service, "confirm_sign_up", MagicMock(return_value={
        "status": "CONFIRMED"
    }))

    monkeypatch.setattr(auth_service, "resend_code", MagicMock(return_value={
        "message": "sent"
    }))

    monkeypatch.setattr(
        auth_service,
        "respond_to_mfa",
        MagicMock(return_value={
            "access_token": "token",
            "id_token": "id",
            "refresh_token": "refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
        }),
    )

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Password123!"

#START TESTS
#SIGNUP
def test_register_user_success(mock_cognito):
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "firstName": "Zaman",
        "lastName": "Bassa",
        "address": "JHB"
    }

    mock_db = MagicMock()

    def refresh(user):
        user.id = "11111111-1111-1111-1111-111111111111"

    mock_db.refresh.side_effect = refresh

    with patch(
        "backend.app.services.auth_service.create_audit_log_item"
    ) as mock_audit:

        result = auth_service.register_user(payload, mock_db)

    assert result["success"] is True
    assert result["data"]["user_sub"] == "abc-123"
    mock_audit.assert_called_once()

#LOGIN
def test_login_success(mock_cognito):
    result = auth_service.authenticate_user({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })

    assert result["success"] is True
    assert result["data"]["access_token"] == "token"
    assert result["data"]["expires_in"] == 3600

#CONFIRM
def test_confirm_user_success(mock_cognito):
    result = auth_service.confirm_user({
        "email": TEST_EMAIL,
        "code": "123456"
    })

    assert result["success"] is True
    assert result["data"]["confirmed"] is True

#RESEND
def test_resend_code_success(mock_cognito):
    result = auth_service.resend_confirmation_code({
        "email": TEST_EMAIL
    })

    assert result["success"] is True

def test_login_requires_mfa(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "login",
        MagicMock(return_value={
            "challenge": "EMAIL_OTP",
            "session": "abc-session",
            "delivery": {
                "medium": "EMAIL",
                "destination": "z***@g***",
            },
        }),
    )

    result = auth_service.authenticate_user({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })

    assert result["success"] is True
    assert result["data"]["mfa_required"] is True
    assert result["data"]["session"] == "abc-session"
    assert result["data"]["delivery"]["medium"] == "EMAIL"

def test_complete_mfa_success(mock_cognito):
    result = auth_service.complete_mfa({
        "email": TEST_EMAIL,
        "session": "abc-session",
        "code": "123456",
    })

    assert result["success"] is True
    assert result["data"]["access_token"] == "token"
    assert result["data"]["id_token"] == "id"
    assert result["data"]["expires_in"] == 3600
#TODO: end to end testing 