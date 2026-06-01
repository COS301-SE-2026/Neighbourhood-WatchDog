import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_internal_detection_ingest(async_client, internal_headers):
    response = {"status": 201, "alert_created": False}

    with patch(
        "app.api.controllers.detection.ingest_detection_handler",
        new=AsyncMock(return_value=response),
    ):
        payload = {
            "camera_id": "22222222-2222-2222-2222-222222222222",
            "frame_timestamp": "2023-01-01T00:00:00Z",
            "detection_type": "HUMAN_PRESENCE",
            "confidence_score": 0.8,
        }
        r = await async_client.post("/internal/detections", json=payload, headers=internal_headers)
        assert r.status_code == 201
        assert r.json()["status"] == 201
