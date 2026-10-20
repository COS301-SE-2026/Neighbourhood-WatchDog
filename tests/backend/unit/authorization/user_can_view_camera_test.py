from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.auth import authorization

CAMERA_ID = uuid4()
PROPERTY_ID = uuid4()
CLAIMS = {"sub": "cognito-user-123"}

def db_result(value): 
    result = MagicMock() 
    result.scalar_one_or_none.return_value = value 
    return result 

def make_db(*results):
    db = MagicMock()
    db.execute = AsyncMock(side_effect=list(results))
    return db

def make_user(role: str = "RESIDENT"):
    user = MagicMock()
    user.system_role.value = role
    return user

def make_camera():
    camera = MagicMock()
    camera.property_id = PROPERTY_ID
    return camera

@pytest.mark.asyncio
@pytest.mark.parametrize("claims", [None, {}, {"sub": None}, {"sub": ""}])
async def test_user_can_view_camera_returns_false_without_sub(claims):
    db = make_db()
    result = await authorization.user_can_view_camera(db, claims, CAMERA_ID)
    assert result is False
    db.execute.assert_not_awaited()

@pytest.mark.asyncio
async def test_user_can_view_camera_returns_false_for_unknown_user():
    db = make_db(db_result(None))
    result = await authorization.user_can_view_camera(db, CLAIMS, CAMERA_ID)
    assert result is False
    assert db.execute.await_count == 1


@pytest.mark.asyncio
async def test_user_can_view_camera_allows_system_admin_without_camera_lookup():
    db = make_db(db_result(make_user("SYSTEM_ADMIN")))
    with patch.object(
        authorization,
        "is_property_member",
        new=AsyncMock(),
    ) as is_member:
        result = await authorization.user_can_view_camera(db, CLAIMS, CAMERA_ID)

    assert result is True
    assert db.execute.await_count == 1
    is_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_can_view_camera_returns_false_for_missing_camera():
    db = make_db(db_result(make_user()), db_result(None))
    with patch.object(
        authorization,
        "is_property_member",
        new=AsyncMock(),
    ) as is_member:
        result = await authorization.user_can_view_camera(db, CLAIMS, CAMERA_ID)
    assert result is False
    is_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_can_view_camera_allows_member_of_cameras_property():
    db = make_db(db_result(make_user()), db_result(make_camera()))
    with patch.object(
        authorization,
        "is_property_member",
        new=AsyncMock(return_value=True),
    ) as is_member:
        result = await authorization.user_can_view_camera(db, CLAIMS, CAMERA_ID)

    assert result is True
    is_member.assert_awaited_once_with(PROPERTY_ID, CLAIMS, db)


@pytest.mark.asyncio
async def test_user_can_view_camera_denies_non_member():
    db = make_db(db_result(make_user()), db_result(make_camera()))
    
    with patch.object(
        authorization,
        "is_property_member",
        new=AsyncMock(return_value=False),
    ):
        result = await authorization.user_can_view_camera(db, CLAIMS, CAMERA_ID)
        
    assert result is False