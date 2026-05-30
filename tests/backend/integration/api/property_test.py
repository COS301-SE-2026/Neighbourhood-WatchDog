import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_get_property_details(async_client, auth_headers):
    detail = {
        "property_id": "11111111-1111-1111-1111-111111111111",
        "address": "123 Test St",
        "property_type": "PRIVATE",
        "created_at": "2021-01-01T00:00:00",
        "users": [],
        "neighbourhood": None,
        "cameras": [],
    }

    with patch(
        "app.api.controllers.property.get_property_details_handler",
        new=AsyncMock(return_value=detail),
    ):
        r = await async_client.get(
            "/properties/11111111-1111-1111-1111-111111111111",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json() == detail
