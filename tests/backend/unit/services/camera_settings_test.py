import pytest
from unittest.mock import MagicMock
from uuid import UUID
from fastapi import HTTPException

from app.services.camera_settings_service import (
    get_camera_settings_handler,
    update_camera_settings_handler,
    create_zone_handler,
    delete_zone_handler,
)

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
    db.execute.return_value = exec_mock
    exec_mock.scalar_one_or_none.return_value = camera
    exec_mock.scalars.return_value.all.return_value = zones or []
    return db


#get_camera_settings_handler 

@pytest.mark.asyncio
async def test_get_settings_returns_threshold_and_zones():
    cam = _mock_camera(0.6)
    zone = _mock_zone()
    db = MagicMock()

    # first execute - camera, 
    # second execute - zones
    db.execute.side_effect = [
        MagicMock(**{"scalar_one_or_none.return_value": cam}),
        MagicMock(**{"scalars.return_value.all.return_value": [zone]}),
    ]

    result = get_camera_settings_handler(CAMERA_ID, db)
    assert result["confidence_threshold"] == pytest.approx(0.6)
    assert len(result["zones"]) == 1
    assert result["zones"][0]["name"] == "Test Zone"


@pytest.mark.asyncio
async def test_get_settings_camera_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        get_camera_settings_handler(CAMERA_ID, db)
    assert exc.value.status_code == 404


#update_camera_settings_handler 

@pytest.mark.asyncio
async def test_update_threshold_ok():
    cam = _mock_camera(0.5)
    db = _make_db(camera=cam)

    result = update_camera_settings_handler(CAMERA_ID, 0.8, db)
    assert cam.confidence_threshold == pytest.approx(0.8)
    db.commit.assert_called_once()
    assert result["confidence_threshold"] == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_update_threshold_camera_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        update_camera_settings_handler(CAMERA_ID, 0.8, db)
    assert exc.value.status_code == 404


#create_zone_handler 

@pytest.mark.asyncio
async def test_create_zone_ok():
    cam = _mock_camera()
    db = _make_db(camera=cam)

    create_zone_handler(CAMERA_ID, "Gate", [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]], db)
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_zone_too_few_points():
    cam = _mock_camera()
    db = _make_db(camera=cam)
    with pytest.raises(HTTPException) as exc:
        create_zone_handler(CAMERA_ID, "Bad Zone", [[0.1, 0.1], [0.5, 0.5]], db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_zone_camera_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        create_zone_handler(CAMERA_ID, "Zone", [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5]], db)
    assert exc.value.status_code == 404


#delete_zone_handler 

@pytest.mark.asyncio
async def test_delete_zone_ok():
    zone = _mock_zone()
    db = _make_db(camera=zone)  # scalar_one_or_none returns the zone
    delete_zone_handler(CAMERA_ID, ZONE_ID, db)
    db.delete.assert_called_once_with(zone)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_zone_not_found():
    db = _make_db(camera=None)
    with pytest.raises(HTTPException) as exc:
        delete_zone_handler(CAMERA_ID, ZONE_ID, db)
    assert exc.value.status_code == 404