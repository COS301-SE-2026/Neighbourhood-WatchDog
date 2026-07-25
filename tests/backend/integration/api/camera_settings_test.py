import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

CAMERA_ID = "40000000-0000-0000-0000-000000000001"
ZONE_ID   = "f68ad3aa-6946-4019-9817-e35d27e15950"
TEST_ZONE_NAME = "Test Zone"

MOCK_SETTINGS = {
    "camera_id": CAMERA_ID,
    "confidence_threshold": 0.5,
    "zones": [],
}

MOCK_ZONE = {
    "id": ZONE_ID,
    "camera_id": CAMERA_ID,
    "name": TEST_ZONE_NAME,
    "polygon": [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]],
}


# GET /cameras/{id}/settings 

@pytest.mark.asyncio
async def test_get_camera_settings_ok(async_client, admin_headers):
    with patch(
        "app.api.controllers.camera_settings.get_camera_settings_handler",
        new=MagicMock(return_value=MOCK_SETTINGS),
    ):
        r = await async_client.get(f"/cameras/{CAMERA_ID}/settings", headers=admin_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["camera_id"] == CAMERA_ID
    assert body["confidence_threshold"] == pytest.approx(0.5)


@pytest.mark.skip(reason="Needs to be refacored")
@pytest.mark.asyncio
async def test_get_camera_settings_resident_forbidden(async_client, auth_headers):
    r = await async_client.get(f"/cameras/{CAMERA_ID}/settings", headers=auth_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_camera_settings_not_found(async_client, admin_headers):
    with patch(
        "app.api.controllers.camera_settings.get_camera_settings_handler",
        new=MagicMock(side_effect=HTTPException(status_code=404, detail="Camera not found")),
    ):
        r = await async_client.get(f"/cameras/{CAMERA_ID}/settings", headers=admin_headers)
    assert r.status_code == 404


# PATCH /cameras/{id}/settings 

@pytest.mark.asyncio
async def test_update_camera_threshold_ok(async_client, admin_headers):
    updated = {"camera_id": CAMERA_ID, "confidence_threshold": 0.7}
    with patch(
        "app.api.controllers.camera_settings.update_camera_settings_handler",
        new=MagicMock(return_value=updated),
    ):
        r = await async_client.patch(
            f"/cameras/{CAMERA_ID}/settings",
            json={"confidence_threshold": 0.7},
            headers=admin_headers,
        )
    assert r.status_code == 200
    assert r.json()["confidence_threshold"] == pytest.approx(0.7)

@pytest.mark.skip(reason="Needs to be refacored")
@pytest.mark.asyncio
async def test_update_camera_threshold_resident_forbidden(async_client, auth_headers):
    r = await async_client.patch(
        f"/cameras/{CAMERA_ID}/settings",
        json={"confidence_threshold": 0.7},
        headers=auth_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_update_camera_threshold_missing_field(async_client, admin_headers):
    with patch(
        "app.api.controllers.camera_settings.update_camera_settings_handler",
        new=MagicMock(return_value={}),
    ):
        r = await async_client.patch(
            f"/cameras/{CAMERA_ID}/settings",
            json={},
            headers=admin_headers,
        )
    assert r.status_code == 400


# POST /cameras/{id}/zones

@pytest.mark.asyncio
async def test_create_zone_ok(async_client, admin_headers):
    with patch(
        "app.api.controllers.camera_settings.create_zone_handler",
        new=MagicMock(return_value=MOCK_ZONE),
    ):
        r = await async_client.post(
            f"/cameras/{CAMERA_ID}/zones",
            json={"name": TEST_ZONE_NAME, "polygon": [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]]},
            headers=admin_headers,
        )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == TEST_ZONE_NAME
    assert body["camera_id"] == CAMERA_ID

@pytest.mark.skip(reason="Needs to be refacored")
@pytest.mark.asyncio
async def test_create_zone_resident_forbidden(async_client, auth_headers):
    r = await async_client.post(
        f"/cameras/{CAMERA_ID}/zones",
        json={"name": "Zone", "polygon": [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5]]},
        headers=auth_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_zone_camera_not_found(async_client, admin_headers):
    with patch(
        "app.api.controllers.camera_settings.create_zone_handler",
        new=MagicMock(side_effect=HTTPException(status_code=404, detail="Camera not found")),
    ):
        r = await async_client.post(
            f"/cameras/{CAMERA_ID}/zones",
            json={"name": "Zone", "polygon": [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5]]},
            headers=admin_headers,
        )
    assert r.status_code == 404


# DELETE /cameras/{id}/zones/{zone_id}

@pytest.mark.asyncio
async def test_delete_zone_ok(async_client, admin_headers):
    with patch(
        "app.api.controllers.camera_settings.delete_zone_handler",
        new=MagicMock(return_value=None),
    ):
        r = await async_client.delete(
            f"/cameras/{CAMERA_ID}/zones/{ZONE_ID}",
            headers=admin_headers,
        )
    assert r.status_code == 204

@pytest.mark.skip(reason="Testing need to be refactored with a more robust roles system")
@pytest.mark.asyncio
async def test_delete_zone_resident_forbidden(async_client, auth_headers):
    r = await async_client.delete(
        f"/cameras/{CAMERA_ID}/zones/{ZONE_ID}",
        headers=auth_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_delete_zone_not_found(async_client, admin_headers):
    with patch(
        "app.api.controllers.camera_settings.delete_zone_handler",
        new=MagicMock(side_effect=HTTPException(status_code=404, detail="Zone not found")),
    ):
        r = await async_client.delete(
            f"/cameras/{CAMERA_ID}/zones/{ZONE_ID}",
            headers=admin_headers,
        )
    assert r.status_code == 404