import pytest
from unittest.mock import AsyncMock, patch

ALERT_TIMESTAMP = "2023-01-01T00:00:00Z"

@pytest.mark.skip(reason="TESTING=true bypasses auth, so this cannot be tested")
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
        new=AsyncMock(return_value=([alert_item],1)),
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

@pytest.mark.asyncio
async def test_list_alerts_default_pagination_params(async_client, auth_headers):
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
        new=AsyncMock(return_value=([alert_item], 1)),
    ) as mock_handler:
        r = await async_client.get(
            "/alerts/55555555-5555-5555-5555-555555555555", headers=auth_headers
        )
    
    assert r.status_code == 200
    _, kwargs = mock_handler.call_args
    assert kwargs["limit"] == 25
    assert kwargs["offset"] == 0
    assert kwargs["status_filter"] is None
    assert kwargs["camera_id"] is None
    assert kwargs["detection_type"] is None

@pytest.mark.asyncio
async def test_list_alerts_forwards_filters(async_client, auth_headers):
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
        new=AsyncMock(return_value=([alert_item], 1)),
    ) as mock_handler:
        r = await async_client.get(
            "/alerts/55555555-5555-5555-5555-555555555555"
            "?status=OPEN"
            "&camera_id=22222222-2222-2222-2222-222222222222"
            "&detection_type=HUMAN_PRESENCE"
            "&start_date=2026-01-01T00:00:00Z"
            "&end_date=2026-12-31T23:59:59Z"
            "&limit=10&offset=20", 
            headers=auth_headers,
        )
    
    assert r.status_code == 200
    body = r.json()
    assert body["data"][0]["status"] == "OPEN"
    assert body["pagination"] == {
        "total": 1,
        "limit": 10,
        "offset": 20,
        "has_more": False,
    }

    _, kwargs = mock_handler.call_args
    assert kwargs["status_filter"] == "OPEN"
    assert str(kwargs["camera_id"]) == "22222222-2222-2222-2222-222222222222"
    assert kwargs["detection_type"] == "HUMAN_PRESENCE"
    assert kwargs["limit"] == 10
    assert kwargs["offset"] == 20

@pytest.mark.asyncio
async def test_list_alerts_rejects_limits_over_max(async_client, auth_headers):
    r = await async_client.get(
         "/alerts/55555555-5555-5555-5555-555555555555?limit=500",
        headers=auth_headers,
    )
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_list_alerts_rejects_negative_offset(async_client, auth_headers):
    r = await async_client.get(
         "/alerts/55555555-5555-5555-5555-555555555555?offset=-1",
        headers=auth_headers,
    )
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_list_alerts_has_more_true_when_pages_remain(async_client, auth_headers):
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
        new=AsyncMock(return_value=([alert_item], 100)),
    ): 
         r = await async_client.get(
         "/alerts/55555555-5555-5555-5555-555555555555?offset=0",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["pagination"]["has_more"] is True
