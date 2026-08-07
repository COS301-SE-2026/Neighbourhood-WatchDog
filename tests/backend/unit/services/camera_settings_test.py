import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import UUID
from fastapi import HTTPException

from app.services.camera_settings_service import (
    get_camera_settings_handler,
    update_camera_settings_handler,
    create_zone_handler,
    delete_zone_handler,
)

@pytest.fixture(autouse=True)
def mock_create_audit_log_item():
    """Prevent camera-settings unit tests from writing real audit records."""
    with patch(
        "app.services.camera_settings_service.create_audit_log_item",
        new_callable=AsyncMock,
    ) as mock_audit_log:
        yield mock_audit_log

CAMERA_ID = UUID("40000000-0000-0000-0000-000000000001")
ZONE_ID   = UUID("f68ad3aa-6946-4019-9817-e35d27e15950")


def _mock_camera(threshold=0.5):
    cam = MagicMock()
    cam.id = CAMERA_ID
    cam.confidence_threshold = threshold
    return cam


def _mock_zone():
    z = MagicMock()
    z.id = ZONE_ID
    z.camera_id = CAMERA_ID
    z.name = "Test Zone"
    z.polygon = [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]]
    return z


def _make_db(camera=None, zones=None):
    db = MagicMock()
    exec_mock = MagicMock()
    exec_mock.scalar_one_or_none.return_value = camera
    exec_mock.scalar.return_value.all.return_value = zones or []

    db.execute = AsyncMock(return_value=exec_mock)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture(autouse=True)
def mock_audit(monkeypatch):
    monkeypatch.setattr(
        "app.services.camera_settings_service.create_audit_log_item",
        MagicMock(),
    )

CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "abc123",
}
#get_camera_settings_handler 

@pytest.mark.asyncio
async def test_get_settings_returns_threshold_and_zones():
    cam = _mock_camera(0.6)
    zone = _mock_zone()
    db = MagicMock()

    # first execute - camera, 
    # second execute - zones
    camera_result = MagicMock()
    camera_result.scalar_one_or_none.return_value = cam

    zones_result = MagicMock()
    zones_result.scalars.return_value.all.return_value = [zone]

    db.execute = AsyncMock(side_effect=[camera_result, zones_result])

    result = await get_camera_settings_handler(CAMERA_ID, db)
    assert result["confidence_threshold"] == pytest.approx(0.6)
    assert len(result["zones"]) == 1
    assert result["zones"][0]["name"] == "Test Zone"


@pytest.mark.asyncio
async def test_get_settings_camera_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        await get_camera_settings_handler(CAMERA_ID, db)
    assert exc.value.status_code == 404


#update_camera_settings_handler 

@pytest.mark.asyncio
async def test_update_threshold_ok():
    cam = _mock_camera(0.5)
    db = _make_db(camera=cam)

    result = await update_camera_settings_handler(CAMERA_ID, 0.8, db, CLAIMS)
    assert cam.confidence_threshold == pytest.approx(0.8)
    db.commit.assert_called_once()
    assert result["confidence_threshold"] == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_update_threshold_camera_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        await update_camera_settings_handler(CAMERA_ID, 0.8, db, CLAIMS)
    assert exc.value.status_code == 404


#create_zone_handler 

@pytest.mark.asyncio
async def test_create_zone_ok():
    cam = _mock_camera()
    db = _make_db(camera=cam)

    await create_zone_handler(CAMERA_ID, "Gate", [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]], db, CLAIMS)
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_zone_too_few_points():
    cam = _mock_camera()
    db = _make_db(camera=cam)
    with pytest.raises(HTTPException) as exc:
        await create_zone_handler(CAMERA_ID, "Bad Zone", [[0.1, 0.1], [0.5, 0.5]], db, CLAIMS)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_zone_camera_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        await create_zone_handler(CAMERA_ID, "Zone", [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5]], db, CLAIMS)
    assert exc.value.status_code == 404


#delete_zone_handler 

@pytest.mark.asyncio
async def test_delete_zone_ok():
    zone = _mock_zone()
    db = _make_db(camera=zone)  # scalar_one_or_none returns the zone
    await delete_zone_handler(CAMERA_ID, ZONE_ID, db, CLAIMS)
    db.delete.assert_called_once_with(zone)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_zone_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        await delete_zone_handler(CAMERA_ID, ZONE_ID, db, CLAIMS)
    assert exc.value.status_code == 404