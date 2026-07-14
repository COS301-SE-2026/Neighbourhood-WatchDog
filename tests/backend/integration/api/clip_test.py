import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_clip_roundtrip(async_client, internal_headers, admin_headers):
    create_payload = {
        "camera_id": "40000000-0000-0000-0000-000000000001",
        "detection_type": "WEAPON_DETECTED",
        "confidence_score": 0.91,
        "frame_timestamp": "2026-07-14T12:00:00+00:00",
    }

    r1 = await async_client.post(
        "/internal/detection-events",
        json=create_payload,
        headers=internal_headers,
    )
    assert r1.status_code == 201
    event_id = r1.json()["detection_event_id"]

    patch_payload = {
        "clip_s3_key": "clips/2026/07/14/test.mp4",
        "clip_expires_at": "2026-07-21T12:00:00+00:00",
    }

    r2 = await async_client.patch(
        f"/internal/detection-events/{event_id}/clip",
        json=patch_payload,
        headers=internal_headers,
    )
    assert r2.status_code == 200

    with patch("app.api.controllers.clips.S3_BUCKET", "test-bucket"), patch(
        "app.api.controllers.clips._s3_client"
    ) as mock_s3_client:
        mock_s3_client.return_value.generate_presigned_url.return_value = "https://signed.example/clip"
        r3 = await async_client.get(f"/api/clips/{event_id}", headers=admin_headers)

    assert r3.status_code == 200
    assert r3.json()["url"] == "https://signed.example/clip"