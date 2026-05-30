import pytest
from unittest.mock import AsyncMock, patch

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
