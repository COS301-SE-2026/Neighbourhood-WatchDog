from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth import authorization


PROPERTY_ID = uuid4()
OTHER_PROPERTY_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()
CAMERA_ID = uuid4()


def db_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_db(*results):
    db = MagicMock()
    db.execute = AsyncMock(side_effect=list(results))
    return db


def make_camera(property_id=PROPERTY_ID):
    camera = MagicMock()
    camera.property_id = property_id
    return camera


def make_property(property_id=PROPERTY_ID):
    property_obj = MagicMock()
    property_obj.id = property_id
    property_obj.neighbourhood_id = NEIGHBOURHOOD_ID
    return property_obj


def claims(role):
    return {
        "id": str(uuid4()),
        "sub": "test-user-sub",
        "custom:role": role,
    }


@pytest.mark.asyncio
async def test_property_admin_can_modify_camera_coverage(monkeypatch):
    checker = authorization.require_camera_authorization(
        "PROPERTY_ADMIN",
        "SYSTEM_ADMIN",
    )

    monkeypatch.setattr(
        authorization,
        "is_property_admin",
        AsyncMock(return_value=True),
    )

    db = make_db(
        db_result(make_camera()),
        db_result(make_property()),
    )

    property_admin_claims = claims("PROPERTY_ADMIN")

    result = await checker(
        CAMERA_ID,
        db,
        property_admin_claims,
    )

    assert result == property_admin_claims


@pytest.mark.asyncio
async def test_system_admin_can_modify_camera_coverage():
    checker = authorization.require_camera_authorization(
        "PROPERTY_ADMIN",
        "SYSTEM_ADMIN",
    )

    db = make_db(
        db_result(make_camera()),
        db_result(make_property()),
    )

    system_admin_claims = claims("SYSTEM_ADMIN")

    result = await checker(
        CAMERA_ID,
        db,
        system_admin_claims,
    )

    assert result == system_admin_claims


@pytest.mark.asyncio
async def test_neighbourhood_admin_cannot_modify_camera_coverage(
    monkeypatch,
):
    checker = authorization.require_camera_authorization(
        "PROPERTY_ADMIN",
        "SYSTEM_ADMIN",
    )

    property_admin_check = AsyncMock(return_value=False)
    neighbourhood_admin_check = AsyncMock(return_value=True)

    monkeypatch.setattr(
        authorization,
        "is_property_admin",
        property_admin_check,
    )
    monkeypatch.setattr(
        authorization,
        "is_neighbourhood_admin",
        neighbourhood_admin_check,
    )

    db = make_db(
        db_result(make_camera()),
        db_result(make_property()),
    )

    with pytest.raises(HTTPException) as exc_info:
        await checker(
            CAMERA_ID,
            db,
            claims("NEIGHBOURHOOD_ADMIN"),
        )

    assert exc_info.value.status_code == 403
    assert "manage this camera" in exc_info.value.detail

    property_admin_check.assert_awaited_once()
    neighbourhood_admin_check.assert_not_awaited()


@pytest.mark.asyncio
async def test_unrelated_property_admin_cannot_modify_camera_coverage(
    monkeypatch,
):
    checker = authorization.require_camera_authorization(
        "PROPERTY_ADMIN",
        "SYSTEM_ADMIN",
    )

    monkeypatch.setattr(
        authorization,
        "is_property_admin",
        AsyncMock(return_value=False),
    )

    db = make_db(
        db_result(make_camera(PROPERTY_ID)),
        db_result(make_property(PROPERTY_ID)),
    )

    with pytest.raises(HTTPException) as exc_info:
        await checker(
            CAMERA_ID,
            db,
            claims("PROPERTY_ADMIN"),
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_property_admin_cannot_modify_camera_from_another_property(
    monkeypatch,
):
    checker = authorization.require_camera_authorization(
        "PROPERTY_ADMIN",
        "SYSTEM_ADMIN",
    )

    property_admin_check = AsyncMock(return_value=False)
    monkeypatch.setattr(
        authorization,
        "is_property_admin",
        property_admin_check,
    )

    db = make_db(
        db_result(make_camera(PROPERTY_ID)),
        db_result(make_property(PROPERTY_ID)),
    )

    with pytest.raises(HTTPException) as exc_info:
        await checker(
            CAMERA_ID,
            db,
            claims("PROPERTY_ADMIN"),
        )

    assert exc_info.value.status_code == 403
    property_admin_check.assert_awaited_once()