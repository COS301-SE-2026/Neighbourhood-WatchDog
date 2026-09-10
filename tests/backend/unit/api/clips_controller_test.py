from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from botocore.exceptions import BotoCoreError
from fastapi import HTTPException

from app.api.controllers import clips
from app.models.camera import CameraVisibilityEnum
from app.models.neighbourhood_user import NeighbourhoodRole
from app.models.user import UserRole


ALERT_ID = uuid4()
CAMERA_ID = uuid4()
PROPERTY_ID = uuid4()
USER_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()


def make_result(*, scalar=None, record=None):
    result = Mock()
    result.scalar_one_or_none.return_value = scalar
    result.one_or_none.return_value = record
    return result


def make_user(
    *,
    system_role=UserRole.RESIDENT,
):
    return SimpleNamespace(
        id=USER_ID,
        system_role=system_role,
    )


def make_camera(
    *,
    visibility=CameraVisibilityEnum.PUBLIC,
):
    return SimpleNamespace(
        id=CAMERA_ID,
        visibility=visibility,
        neighbourhood_id=NEIGHBOURHOOD_ID,
    )


def make_property(
    *,
    neighbourhood_id=NEIGHBOURHOOD_ID,
):
    return SimpleNamespace(
        id=PROPERTY_ID,
        neighbourhood_id=neighbourhood_id,
    )


def make_alert(
    *,
    clip_s3_key="clips/example.mp4",
    clip_expires_at=None,
):
    return SimpleNamespace(
        id=ALERT_ID,
        camera_id=CAMERA_ID,
        clip_s3_key=clip_s3_key,
        clip_expires_at=clip_expires_at,
    )


@pytest.mark.asyncio
async def test_check_rbac_rejects_missing_identity():
    camera = make_camera()
    property_obj = make_property()
    db = Mock()

    with pytest.raises(HTTPException) as exc_info:
        await clips._check_rbac(
            claims={},
            camera=camera,
            property_obj=property_obj,
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "Authenticated user identity is missing."
    )
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_check_rbac_rejects_unknown_application_user():
    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(scalar=None)
    )

    with pytest.raises(HTTPException) as exc_info:
        await clips._check_rbac(
            claims={"sub": "unknown-sub"},
            camera=make_camera(),
            property_obj=make_property(),
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "No application user is associated with this identity."
    )
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_rbac_allows_system_admin_without_more_queries():
    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(
            scalar=make_user(system_role=UserRole.SYSTEM_ADMIN)
        )
    )

    result = await clips._check_rbac(
        claims={"sub": "system-admin-sub"},
        camera=make_camera(
            visibility=CameraVisibilityEnum.PRIVATE
        ),
        property_obj=make_property(),
        db=db,
    )

    assert result is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_rbac_allows_property_admin():
    user = make_user()
    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            make_result(scalar=user),
            make_result(scalar=SimpleNamespace()),
        ]
    )

    result = await clips._check_rbac(
        claims={"sub": "property-admin-sub"},
        camera=make_camera(
            visibility=CameraVisibilityEnum.PRIVATE
        ),
        property_obj=make_property(),
        db=db,
    )

    assert result is None
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_check_rbac_rejects_camera_without_neighbourhood():
    user = make_user()
    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(scalar=user)
    )

    with pytest.raises(HTTPException) as exc_info:
        await clips._check_rbac(
            claims={"sub": "resident-sub"},
            camera=make_camera(),
            property_obj=make_property(neighbourhood_id=None),
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "This camera is not associated with a neighbourhood."
    )
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_rbac_rejects_user_without_neighbourhood_membership():
    user = make_user()
    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            make_result(scalar=user),
            make_result(scalar=None),
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await clips._check_rbac(
            claims={"sub": "resident-sub"},
            camera=make_camera(),
            property_obj=make_property(),
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "You do not belong to this camera's neighbourhood."
    )
    assert db.execute.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role",
    [
        NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
        NeighbourhoodRole.SECURITY_OFFICER,
    ],
)
async def test_check_rbac_allows_neighbourhood_admin_and_security_officer(role):
    user = make_user()
    membership = SimpleNamespace(role=role)

    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            make_result(scalar=user),
            make_result(scalar=None),
            make_result(scalar=membership),
        ]
    )

    result = await clips._check_rbac(
        claims={"sub": "member-sub"},
        camera=make_camera(
            visibility=CameraVisibilityEnum.PRIVATE
        ),
        property_obj=make_property(),
        db=db,
    )

    assert result is None
    assert db.execute.await_count == 3


@pytest.mark.asyncio
async def test_check_rbac_allows_resident_to_view_public_camera():
    user = make_user()
    membership = SimpleNamespace(
        role=NeighbourhoodRole.RESIDENT
    )

    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            make_result(scalar=user),
            make_result(scalar=None),
            make_result(scalar=membership),
        ]
    )

    result = await clips._check_rbac(
        claims={"sub": "resident-sub"},
        camera=make_camera(
            visibility=CameraVisibilityEnum.PUBLIC
        ),
        property_obj=make_property(),
        db=db,
    )

    assert result is None
    assert db.execute.await_count == 3


@pytest.mark.asyncio
async def test_check_rbac_rejects_resident_from_restricted_camera():
    user = make_user()
    membership = SimpleNamespace(
        role=NeighbourhoodRole.RESIDENT
    )

    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            make_result(scalar=user),
            make_result(scalar=None),
            make_result(scalar=membership),
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await clips._check_rbac(
            claims={"sub": "resident-sub"},
            camera=make_camera(
                visibility=CameraVisibilityEnum.RESTRICTED
            ),
            property_obj=make_property(),
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "Residents can only view public-camera footage."
    )


@pytest.mark.asyncio
async def test_check_rbac_rejects_unknown_membership_role():
    user = make_user()
    membership = SimpleNamespace(role="UNKNOWN_ROLE")

    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            make_result(scalar=user),
            make_result(scalar=None),
            make_result(scalar=membership),
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await clips._check_rbac(
            claims={"sub": "member-sub"},
            camera=make_camera(),
            property_obj=make_property(),
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "Insufficient permissions to view footage."
    )


@pytest.mark.asyncio
async def test_get_clip_url_rejects_unconfigured_s3_storage():
    db = Mock()

    with patch.object(clips, "S3_BUCKET", ""):
        with pytest.raises(HTTPException) as exc_info:
            await clips.get_clip_url(
                alert_id=ALERT_ID,
                db=db,
                claims={"sub": "user-sub"},
            )

    assert exc_info.value.status_code == 503
    assert "storage" in exc_info.value.detail.lower()
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_get_clip_url_returns_404_when_alert_record_is_missing():
    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(record=None)
    )

    with patch.object(clips, "S3_BUCKET", "watchdog-clips"):
        with pytest.raises(HTTPException) as exc_info:
            await clips.get_clip_url(
                alert_id=ALERT_ID,
                db=db,
                claims={"sub": "user-sub"},
            )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == (
        "Alert or associated camera/property was not found."
    )


@pytest.mark.asyncio
async def test_get_clip_url_returns_404_when_alert_has_no_clip():
    alert = make_alert(clip_s3_key=None)
    record = (alert, make_camera(), make_property())

    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(record=record)
    )

    with patch.object(clips, "S3_BUCKET", "watchdog-clips"):
        with pytest.raises(HTTPException) as exc_info:
            await clips.get_clip_url(
                alert_id=ALERT_ID,
                db=db,
                claims={"sub": "user-sub"},
            )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == (
        "No clip is available for this alert."
    )


@pytest.mark.asyncio
async def test_get_clip_url_returns_410_when_clip_has_expired():
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    alert = make_alert(clip_expires_at=expired_at)
    record = (alert, make_camera(), make_property())

    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(record=record)
    )

    with patch.object(clips, "S3_BUCKET", "watchdog-clips"):
        with pytest.raises(HTTPException) as exc_info:
            await clips.get_clip_url(
                alert_id=ALERT_ID,
                db=db,
                claims={"sub": "user-sub"},
            )

    assert exc_info.value.status_code == 410
    assert exc_info.value.detail == (
        "This clip has expired and is no longer available."
    )


@pytest.mark.asyncio
async def test_get_clip_url_generates_presigned_url():
    future_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    alert = make_alert(
        clip_s3_key="clips/security-event.mp4",
        clip_expires_at=future_expiry,
    )
    camera = make_camera()
    property_obj = make_property()
    record = (alert, camera, property_obj)

    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(record=record)
    )

    s3_client = Mock()
    s3_client.generate_presigned_url.return_value = (
        "https://s3.example.com/presigned-url"
    )

    with (
        patch.object(clips, "S3_BUCKET", "watchdog-clips"),
        patch.object(
            clips,
            "_check_rbac",
            new=AsyncMock(),
        ) as check_rbac,
        patch.object(
            clips,
            "_s3_client",
            return_value=s3_client,
        ),
    ):
        response = await clips.get_clip_url(
            alert_id=ALERT_ID,
            db=db,
            claims={"sub": "user-sub"},
        )

    assert response == {
        "url": "https://s3.example.com/presigned-url",
        "expires_in": clips.PRESIGN_TTL,
    }

    check_rbac.assert_awaited_once_with(
        claims={"sub": "user-sub"},
        camera=camera,
        property_obj=property_obj,
        db=db,
    )

    s3_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={
            "Bucket": "watchdog-clips",
            "Key": "clips/security-event.mp4",
        },
        ExpiresIn=clips.PRESIGN_TTL,
    )


@pytest.mark.asyncio
async def test_get_clip_url_returns_503_when_s3_presigning_fails():
    alert = make_alert(
        clip_s3_key="clips/security-event.mp4",
        clip_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    record = (alert, make_camera(), make_property())

    db = Mock()
    db.execute = AsyncMock(
        return_value=make_result(record=record)
    )

    s3_client = Mock()
    s3_client.generate_presigned_url.side_effect = BotoCoreError()

    with (
        patch.object(clips, "S3_BUCKET", "watchdog-clips"),
        patch.object(
            clips,
            "_check_rbac",
            new=AsyncMock(),
        ),
        patch.object(
            clips,
            "_s3_client",
            return_value=s3_client,
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await clips.get_clip_url(
                alert_id=ALERT_ID,
                db=db,
                claims={"sub": "user-sub"},
            )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "Could not generate a temporary clip URL."
    )