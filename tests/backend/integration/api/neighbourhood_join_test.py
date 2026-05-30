import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_join_neighbourhood(async_client, auth_headers):
    result = {
        "id": "66666666-6666-6666-6666-666666666666",
        "neighbourhood_id": "55555555-5555-5555-5555-555555555555",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "status": "PENDING",
        "created_at": "2023-01-01T00:00:00Z",
    }

    with patch(
        "app.api.controllers.neighbourhood_join.request_to_join_handler",
        new=AsyncMock(return_value=result),
    ):
        payload = {"join_code": "ABC123"}
        r = await async_client.post("/neighbourhood/join", json=payload, headers=auth_headers)
        assert r.status_code == 201
        body = r.json()
        assert body["status"] == 201
        assert body["data"]["id"] == result["id"]


@pytest.mark.asyncio
async def test_resolve_join_request(async_client, admin_headers):
    result = {
        "id": "66666666-6666-6666-6666-666666666666",
        "neighbourhood_id": "55555555-5555-5555-5555-555555555555",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "status": "APPROVE",
        "created_at": "2023-01-01T00:00:00Z",
    }

    with patch(
        "app.api.controllers.neighbourhood_join.resolve_join_request_handler",
        new=AsyncMock(return_value=result),
    ):
        payload = {"action": "APPROVE"}
        r = await async_client.patch(
            "/neighbourhood/join-requests/66666666-6666-6666-6666-666666666666",
            json=payload,
            headers=admin_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == 200
        assert body["data"]["id"] == result["id"]
