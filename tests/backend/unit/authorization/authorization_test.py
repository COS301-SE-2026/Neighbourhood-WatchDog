from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth import authorization


PROPERTY_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()
CAMERA_ID = uuid4()

CLAIMS = {
    "id": str(uuid4()),
    "sub": "cognito-user-123",
}

SYSTEM_ADMIN_CLAIMS = {
    **CLAIMS,
    "custom:role": "SYSTEM_ADMIN",
}


def db_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_db(*results):
    db = MagicMock()
    db.execute = AsyncMock(side_effect=list(results))
    return db


@pytest.mark.asyncio
async def test_is_property_admin_returns_false_without_user_sub():
    db = MagicMock()
    db.execute = AsyncMock()

    result = await authorization.is_property_admin(
        PROPERTY_ID,
        {},
        db,
    )

    assert result is False
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_is_property_admin_returns_true_for_admin_membership():
    db = make_db(db_result(MagicMock()))

    result = await authorization.is_property_admin(
        PROPERTY_ID,
        CLAIMS,
        db,
    )

    assert result is True
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_property_admin_returns_false_for_non_admin():
    db = make_db(db_result(None))

    result = await authorization.is_property_admin(
        PROPERTY_ID,
        CLAIMS,
        db,
    )

    assert result is False


@pytest.mark.asyncio
async def test_is_property_member_returns_false_without_claims():
    db = MagicMock()
    db.execute = AsyncMock()

    result = await authorization.is_property_member(
        PROPERTY_ID,
        {},
        db,
    )

    assert result is False
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_is_property_member_returns_true_for_membership():
    db = make_db(db_result(MagicMock()))

    result = await authorization.is_property_member(
        PROPERTY_ID,
        CLAIMS,
        db,
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_property_member_returns_false_without_membership():
    db = make_db(db_result(None))

    result = await authorization.is_property_member(
        PROPERTY_ID,
        CLAIMS,
        db,
    )

    assert result is False


@pytest.mark.asyncio
async def test_is_neighbourhood_admin_returns_false_without_neighbourhood_id():
    db = MagicMock()
    db.execute = AsyncMock()

    result = await authorization.is_neighbourhood_admin(
        None,
        CLAIMS,
        db,
    )

    assert result is False
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_is_neighbourhood_admin_returns_true_for_admin():
    db = make_db(db_result(MagicMock()))

    result = await authorization.is_neighbourhood_admin(
        NEIGHBOURHOOD_ID,
        CLAIMS,
        db,
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_neighbourhood_member_returns_true_for_membership():
    db = make_db(db_result(MagicMock()))

    result = await authorization.is_neighbourhood_member(
        NEIGHBOURHOOD_ID,
        CLAIMS,
        db,
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_neighbourhood_member_returns_false_without_membership():
    db = make_db(db_result(None))

    result = await authorization.is_neighbourhood_member(
        NEIGHBOURHOOD_ID,
        CLAIMS,
        db,
    )

    assert result is False


@pytest.mark.asyncio
async def test_require_property_member_allows_system_admin():
    checker = authorization.require_property_member()

    db = MagicMock()
    db.execute = AsyncMock()

    result = await checker(
        PROPERTY_ID,
        db,
        SYSTEM_ADMIN_CLAIMS,
    )

    assert result == SYSTEM_ADMIN_CLAIMS
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_require_property_member_allows_property_member(monkeypatch):
    checker = authorization.require_property_member()

    membership_check = AsyncMock(return_value=True)
    monkeypatch.setattr(
        authorization,
        "is_property_member",
        membership_check,
    )

    result = await checker(
        PROPERTY_ID,
        MagicMock(),
        CLAIMS,
    )

    assert result == CLAIMS
    membership_check.assert_awaited_once()


@pytest.mark.asyncio
async def test_require_property_member_rejects_non_member(monkeypatch):
    checker = authorization.require_property_member()

    monkeypatch.setattr(
        authorization,
        "is_property_member",
        AsyncMock(return_value=False),
    )

    with pytest.raises(HTTPException) as exc:
        await checker(
            PROPERTY_ID,
            MagicMock(),
            CLAIMS,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_neighbourhood_member_allows_system_admin():
    checker = authorization.require_neighbourhood_member()

    result = await checker(
        NEIGHBOURHOOD_ID,
        MagicMock(),
        SYSTEM_ADMIN_CLAIMS,
    )

    assert result == SYSTEM_ADMIN_CLAIMS


@pytest.mark.asyncio
async def test_require_neighbourhood_member_rejects_non_member(monkeypatch):
    checker = authorization.require_neighbourhood_member()

    monkeypatch.setattr(
        authorization,
        "is_neighbourhood_member",
        AsyncMock(return_value=False),
    )

    with pytest.raises(HTTPException) as exc:
        await checker(
            NEIGHBOURHOOD_ID,
            MagicMock(),
            CLAIMS,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_property_authorization_returns_404_for_missing_property():
    checker = authorization.require_property_authorization(
        "PROPERTY_ADMIN",
    )

    db = make_db(db_result(None))

    with pytest.raises(HTTPException) as exc:
        await checker(
            PROPERTY_ID,
            db,
            CLAIMS,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_require_property_authorization_rejects_unauthorized_user(
    monkeypatch,
):
    checker = authorization.require_property_authorization(
        "PROPERTY_ADMIN",
    )

    property_obj = MagicMock()
    property_obj.id = PROPERTY_ID
    property_obj.neighbourhood_id = NEIGHBOURHOOD_ID

    monkeypatch.setattr(
        authorization,
        "_has_required_permission",
        AsyncMock(return_value=False),
    )

    db = make_db(db_result(property_obj))

    with pytest.raises(HTTPException) as exc:
        await checker(
            PROPERTY_ID,
            db,
            CLAIMS,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_camera_authorization_returns_404_for_missing_camera():
    checker = authorization.require_camera_authorization(
        "PROPERTY_ADMIN",
    )

    db = make_db(db_result(None))

    with pytest.raises(HTTPException) as exc:
        await checker(
            CAMERA_ID,
            db,
            CLAIMS,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_require_camera_authorization_rejects_unauthorized_user(
    monkeypatch,
):
    checker = authorization.require_camera_authorization(
        "PROPERTY_ADMIN",
    )

    camera = MagicMock()
    camera.property_id = PROPERTY_ID

    property_obj = MagicMock()
    property_obj.id = PROPERTY_ID
    property_obj.neighbourhood_id = NEIGHBOURHOOD_ID

    monkeypatch.setattr(
        authorization,
        "_has_required_permission",
        AsyncMock(return_value=False),
    )

    db = make_db(
        db_result(camera),
        db_result(property_obj),
    )

    with pytest.raises(HTTPException) as exc:
        await checker(
            CAMERA_ID,
            db,
            CLAIMS,
        )

    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_is_property_member_returns_false_without_sub():
    db = MagicMock()
    db.execute = AsyncMock()

    result = await authorization.is_property_member(
        PROPERTY_ID,
        {"id": "user-id"},
        db,
    )

    assert result is False
    db.execute.assert_not_awaited()

@pytest.mark.asyncio
async def test_is_neighbourhood_member_returns_false_without_sub():
    db = MagicMock()
    db.execute = AsyncMock()

    result = await authorization.is_neighbourhood_member(
        NEIGHBOURHOOD_ID,
        {"id": "user-id"},
        db,
    )

    assert result is False
    db.execute.assert_not_awaited()

@pytest.mark.asyncio
async def test_required_permission_allows_system_admin():
    result = await authorization._has_required_permission(
        ("SYSTEM_ADMIN",),
        PROPERTY_ID,
        NEIGHBOURHOOD_ID,
        SYSTEM_ADMIN_CLAIMS,
        MagicMock(),
    )

    assert result is True

@pytest.mark.asyncio
async def test_required_permission_allows_property_admin(
    monkeypatch,
):
    monkeypatch.setattr(
        authorization,
        "is_property_admin",
        AsyncMock(return_value=True),
    )

    result = await authorization._has_required_permission(
        ("PROPERTY_ADMIN",),
        PROPERTY_ID,
        NEIGHBOURHOOD_ID,
        CLAIMS,
        MagicMock(),
    )

    assert result is True

@pytest.mark.asyncio
async def test_required_permission_allows_neighbourhood_admin(
    monkeypatch,
):
    monkeypatch.setattr(
        authorization,
        "is_property_admin",
        AsyncMock(return_value=False),
    )
    monkeypatch.setattr(
        authorization,
        "is_neighbourhood_admin",
        AsyncMock(return_value=True),
    )

    result = await authorization._has_required_permission(
        ("NEIGHBOURHOOD_ADMIN",),
        PROPERTY_ID,
        NEIGHBOURHOOD_ID,
        CLAIMS,
        MagicMock(),
    )

    assert result is True

@pytest.mark.asyncio
async def test_required_permission_rejects_user_without_permission(
    monkeypatch,
):
    monkeypatch.setattr(
        authorization,
        "is_property_admin",
        AsyncMock(return_value=False),
    )
    monkeypatch.setattr(
        authorization,
        "is_neighbourhood_admin",
        AsyncMock(return_value=False),
    )

    result = await authorization._has_required_permission(
        (
            "PROPERTY_ADMIN",
            "NEIGHBOURHOOD_ADMIN",
        ),
        PROPERTY_ID,
        NEIGHBOURHOOD_ID,
        CLAIMS,
        MagicMock(),
    )

    assert result is False