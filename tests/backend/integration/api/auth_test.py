import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.auth import cognito


@pytest.mark.asyncio
async def test_get_me_returns_user(async_client, auth_headers):
    user = {"id": "11111111-1111-1111-1111-111111111111", "email": "dev@local.test"}
    with patch("app.api.controllers.auth.create_user", new=AsyncMock(return_value=user)):
        r = await async_client.get("/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == user


@pytest.mark.asyncio
async def test_logout(async_client, auth_headers):
    r = await async_client.post("/auth/logout", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"message": "Logged out"}

# MOCK AWS BOTO3 LAYER
@pytest.fixture(autouse=True)
def mock_cognito_client(monkeypatch):

    mock_client = MagicMock()

    # SIGNUP
    mock_client.sign_up.return_value = {
        "UserSub": "abc-123",
        "UserConfirmed": False
    }

    # LOGIN
    mock_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "token-123",
            "IdToken": "id-123",
            "RefreshToken": "refresh-123",
            "ExpiresIn": 3600,
            "TokenType": "Bearer"
        }
    }

    # CONFIRM
    mock_client.confirm_sign_up.return_value = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }

    # RESEND
    mock_client.resend_confirmation_code.return_value = {
        "CodeDeliveryDetails": {"Destination": "email"}
    }

    
    monkeypatch.setattr(# mock AWS boundary
        cognito,
        "get_cognito_client",
        lambda: mock_client
    )


#DATA
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Password123!"

#INTEGRATION TEST
#SIGNUP
def test_register_user_integration(async_client):
    response = async_client.post("/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": "Zaman",
        "address": "JHB"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["user_sub"] == "abc-123"


#LOGIN
def test_login_integration(async_client):
    response = async_client.post("/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })

    assert response.status_code == 200
    data = response.json()

    assert data["access_token"] == "token-123"
    assert data["id_token"] == "id-123"
    assert data["expires_in"] == 3600

#CONFIRM
def test_confirm_sign_up_integration(async_client):
    response = async_client.post("/auth/confirm", json={
        "email": TEST_EMAIL,
        "code": "123456"
    })

    assert response.status_code == 200
    data = response.json()

    assert "message" in data


#RESEND
def test_resend_code_integration(async_client):
    response = async_client.post("/auth/resend-code", json={
        "email": TEST_EMAIL
    })

    assert response.status_code == 200
    data = response.json()

    assert "message" in data