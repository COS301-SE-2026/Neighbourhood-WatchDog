import pytest
from unittest.mock import AsyncMock, patch

from app import app
from app.core.celery_app import celery

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

@pytest.fixture
def fake_clip_bytes() -> bytes:
    """Generates a fake mp4 clip for the test"""
    return b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1024

@pytest.fixture
def celery_eager_mode():
    celery.conf.task_always_eager = True
    celery.conf.task_eager_propogates = True
    yield
    celery.conf.task_always_eager = False
    celery.conf.task_eager_propogates = False

