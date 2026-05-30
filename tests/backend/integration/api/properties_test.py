import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

TEST_ADDRESS = "123 Test St"

@pytest.mark.asyncio
async def test_create_property_happy_path(async_client, auth_headers):
    new_prop = SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        neighbourhood_id=None,
        address=TEST_ADDRESS,
        property_type="PRIVATE",
        created_at="2021-01-01T00:00:00",
    )

    with patch(
        "app.api.controllers.property.create_property_handler",
        new=AsyncMock(return_value=new_prop),
    ):
        payload = {"address": TEST_ADDRESS, "property_type": "PRIVATE"}
        r = await async_client.post("/properties/create-property", json=payload, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == 201
        assert body["data"]["address"] == TEST_ADDRESS


@pytest.mark.asyncio
async def test_create_property_unauthorized(async_client):
    payload = {"address": TEST_ADDRESS, "property_type": "PRIVATE"}
    r = await async_client.post("/properties/create-property", json=payload)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_my_properties(async_client, auth_headers):
    mock_prop = SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        neighbourhood_id=None,
        address=TEST_ADDRESS,
        property_type="PRIVATE",
        created_at="2021-01-01T00:00:00",
    )

    with patch(
        "app.api.controllers.property.get_user_properties_handler",
        new=AsyncMock(return_value=[mock_prop]),
    ):
        r = await async_client.get("/properties/my-properties", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert body[0]["address"] == TEST_ADDRESS
