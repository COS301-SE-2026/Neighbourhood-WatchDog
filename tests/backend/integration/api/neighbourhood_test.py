import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_neighbourhood(async_client, auth_headers):
    new_nb = {
        "id": "55555555-5555-5555-5555-555555555555",
        "name": "TestVille",
        "location": "Test Area",
        "join_code": "ABC123",
        "created_at": "2021-01-01T00:00:00",
    }

    with patch(
        "app.api.controllers.neighbourhood.create_neighbourhood_handler",
        new=AsyncMock(return_value=new_nb),
    ):
        payload = {"name": "TestVille", "location": "Test Area", "property_id": "11111111-1111-1111-1111-111111111111"}
        r = await async_client.post("/neighbourhood/create-neighbourhood", json=payload, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == 201
        assert body["data"]["name"] == "TestVille"
