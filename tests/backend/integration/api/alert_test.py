import pytest
from unittest.mock import AsyncMock, patch

ALERT_TIMESTAMP = "2023-01-01T00:00:00Z"

@pytest.mark.asyncio
async def test_create_alert(async_client, auth_headers):
    alert_res = {
        "id": "77777777-7777-7777-7777-777777777777",
        "camera_id": "22222222-2222-2222-2222-222222222222",
        "detection_event_id": "88888888-8888-8888-8888-888888888888",
        "status": "OPEN",
        "created_at": ALERT_TIMESTAMP,
    }

    with patch(
        "app.api.controllers.alert.alert_service.create_alert",
        new=AsyncMock(return_value=alert_res),
    ):
        payload = {
            "camera_id": "22222222-2222-2222-2222-222222222222",
            "detection_type": "HUMAN_PRESENCE",
            "confidence": 0.9,
            "timestamp": ALERT_TIMESTAMP,
        }
        r = await async_client.post("/alerts/", json=payload, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == alert_res["id"]


@pytest.mark.asyncio
async def test_dev_broadcast(async_client, auth_headers):
    payload = {"neighbourhood_id": "5555", "camera_id": "2222", "detection_type": "HUMAN_PRESENCE", "confidence": 0.5}
    r = await async_client.post("/alerts/dev/broadcast", json=payload, headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"status": "broadcasted"}


@pytest.mark.asyncio
async def test_list_and_acknowledge(async_client, auth_headers):
    alert_item = {
        "id": "77777777-7777-7777-7777-777777777777",
        "camera_id": "22222222-2222-2222-2222-222222222222",
        "detection_event_id": "88888888-8888-8888-8888-888888888888",
        "status": "OPEN",
        "resolved_by": None,
        "resolved_at": None,
        "created_at": ALERT_TIMESTAMP,
        "detection_type": "HUMAN_PRESENCE",
        "confidence_score": 0.9,
        "thumbnail_url": None,
    }

    with patch(
        "app.api.controllers.alert.list_alerts_handler",
        new=AsyncMock(return_value=[alert_item]),
    ), patch(
        "app.api.controllers.alert.acknowledge_alert_handler",
        new=AsyncMock(return_value=alert_item),
    ):
        r = await async_client.get("/alerts/55555555-5555-5555-5555-555555555555", headers=auth_headers)
        assert r.status_code == 200

        r2 = await async_client.patch(
            "/alerts/77777777-7777-7777-7777-777777777777/acknowledge", headers=auth_headers
        )
        assert r2.status_code == 200
        assert r2.json()["data"]["id"] == alert_item["id"]
