import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

RSTP_URL = "rtsp://example.com/stream"
LOCATION = "Front Door"

@pytest.mark.asyncio
async def test_register_camera(async_client, auth_headers):
    mock_camera = {
        "id": "22222222-2222-2222-2222-222222222222",
        "property_id": "33333333-3333-3333-3333-333333333333",
        "neighbourhood_id": "44444444-4444-4444-4444-444444444444",
        "visibility": "PRIVATE",
        "location": LOCATION,
        "rtsp_url": RSTP_URL,
        "created_at": "2021-01-01T00:00:00",
    }

    with patch(
        "app.api.controllers.camera.register_camera_handler",
        new=AsyncMock(return_value=mock_camera),
    ):
        payload = {
            "rtsp_url": RSTP_URL,
            "location": LOCATION,
            "visibility": "PRIVATE",
            "property_id": "33333333-3333-3333-3333-333333333333",
        }
        r = await async_client.post("/camera/register-camera", json=payload, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == 201
        assert body["data"]["location"] == LOCATION


@pytest.mark.asyncio
async def test_get_property_cameras(async_client, auth_headers):
    camera_res = {
        "id": "22222222-2222-2222-2222-222222222222",
        "property_id": "33333333-3333-3333-3333-333333333333",
        "neighbourhood_id": "44444444-4444-4444-4444-444444444444",
        "visibility": "PRIVATE",
        "location": LOCATION,
        "rtsp_url": RSTP_URL,
        "created_at": "2021-01-01T00:00:00",
    }

    with patch(
        "app.api.controllers.camera.list_cameras_handler",
        new=AsyncMock(return_value={"status": 200, "message": "ok", "data": [camera_res]}),
    ):
        r = await async_client.get(
            "/camera/property/33333333-3333-3333-3333-333333333333",
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == 200 or body.get("data") is not None
