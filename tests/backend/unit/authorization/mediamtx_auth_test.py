from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.camera import MediaMtxAuthRequest
from app.services.camera_service import (
    _enabled_camera_from_path,
    authorize_mediamtx_for_agent_handler,
)


CAMERA_ID = uuid4()
CAMERA_PATH = f"cameras/{CAMERA_ID}"
CLAIMS = {"sub": "cognito-user-123"}


def make_request(**overrides) -> MediaMtxAuthRequest:
    values = {
        "user": "jwt",
        "password": "viewer-token",
        "action": "read",
        "path": CAMERA_PATH,
        "protocol": "webrtc",
    }
    values.update(overrides)
    return MediaMtxAuthRequest(**values)


def make_camera():
    camera = MagicMock()
    camera.id = CAMERA_ID
    return camera


def db_returning(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value

    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    return db


# read (viewers)

@pytest.mark.asyncio
async def test_read_with_valid_token_for_allowed_viewer_returns_204():
    db = MagicMock()

    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch(
            "app.services.camera_service.verify_jwt",
            return_value=CLAIMS,
        ) as verify_jwt,
        patch(
            "app.services.camera_service.user_can_view_camera",
            new=AsyncMock(return_value=True),
        ) as can_view,
    ):
        response = await authorize_mediamtx_for_agent_handler(make_request(), db)

    assert response.status_code == 204
    verify_jwt.assert_called_once_with("viewer-token")
    can_view.assert_awaited_once_with(db, CLAIMS, CAMERA_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user", "password"),
    [
        ("", ""),  # RTSP clients send empty credentials first
        ("jwt", ""),
        ("someone-else", "viewer-token"),
    ],
)
async def test_read_without_jwt_credentials_returns_401(user, password):
    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch("app.services.camera_service.verify_jwt") as verify_jwt,
    ):
        with pytest.raises(HTTPException) as exc:
            await authorize_mediamtx_for_agent_handler(
                make_request(user=user, password=password),
                MagicMock(),
            )

    assert exc.value.status_code == 401
    verify_jwt.assert_not_called()


@pytest.mark.asyncio
async def test_read_with_invalid_token_returns_401():
    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch(
            "app.services.camera_service.verify_jwt",
            side_effect=HTTPException(status_code=401, detail="Invalid token"),
        ),
        patch(
            "app.services.camera_service.user_can_view_camera",
            new=AsyncMock(),
        ) as can_view,
    ):
        with pytest.raises(HTTPException) as exc:
            await authorize_mediamtx_for_agent_handler(make_request(), MagicMock())

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid viewer token."
    can_view.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_by_user_without_camera_access_returns_401():
    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch("app.services.camera_service.verify_jwt", return_value=CLAIMS),
        patch(
            "app.services.camera_service.user_can_view_camera",
            new=AsyncMock(return_value=False),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await authorize_mediamtx_for_agent_handler(make_request(), MagicMock())

    assert exc.value.status_code == 401
    assert exc.value.detail == "Not allowed to view this camera."


# publish (edge agents) 


@pytest.mark.asyncio
async def test_publish_with_valid_camera_credentials_returns_204():
    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch(
            "app.services.camera_service._camera_publish_credentials",
            return_value=("camera-user", "camera-password"),
        ) as credentials,
    ):
        response = await authorize_mediamtx_for_agent_handler(
            make_request(
                action="publish",
                user="camera-user",
                password="camera-password",
                protocol="rtsp",
            ),
            MagicMock(),
        )

    assert response.status_code == 204
    credentials.assert_called_once_with(str(CAMERA_ID))


@pytest.mark.asyncio
async def test_read_with_camera_publish_credentials_returns_204():
    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch(
            "app.services.camera_service._camera_publish_credentials",
            return_value=("camera-user", "camera-password"),
        ),
    ):
        response = await authorize_mediamtx_for_agent_handler(
            make_request(action="read", user="camera-user", password="camera-password", protocol="rtsp"),
            MagicMock(),
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_read_with_wrong_camera_password_returns_401():
    request = make_request(action="read", user="camera-user", password="wrong", protocol="rtsp")
    db = MagicMock()

    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch(
            "app.services.camera_service._camera_publish_credentials",
            return_value=("camera-user", "camera-password"),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await authorize_mediamtx_for_agent_handler(request, db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user", "password"),
    [
        ("camera-user", "wrong-password"),
        ("wrong-user", "camera-password"),
        ("", ""),
    ],
)
async def test_publish_with_invalid_credentials_returns_401(user, password):
    with (
        patch(
            "app.services.camera_service._enabled_camera_from_path",
            new=AsyncMock(return_value=make_camera()),
        ),
        patch(
            "app.services.camera_service._camera_publish_credentials",
            return_value=("camera-user", "camera-password"),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await authorize_mediamtx_for_agent_handler(
                make_request(action="publish", user=user, password=password),
                MagicMock(),
            )

    assert exc.value.status_code == 401


# everything else


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action",
    [
        "playback",
        "api",
        "metrics",
        "",  # an empty action must not be approved
        "re",  # substrings of "read" must not match
        "play",  # substrings of "playback" must not match
    ],
)
async def test_other_actions_return_403(action):
    with patch(
        "app.services.camera_service._enabled_camera_from_path",
        new=AsyncMock(),
    ) as camera_lookup:
        with pytest.raises(HTTPException) as exc:
            await authorize_mediamtx_for_agent_handler(
                make_request(action=action),
                MagicMock(),
            )

    assert exc.value.status_code == 403
    camera_lookup.assert_not_awaited()


# _enabled_camera_from_path


@pytest.mark.asyncio
async def test_enabled_camera_from_path_returns_camera():
    camera = make_camera()
    db = db_returning(camera)

    result = await _enabled_camera_from_path(CAMERA_PATH, db)

    assert result is camera
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "",
        "cameras/",
        "cameras/not-a-uuid",
        f"other/{CAMERA_ID}",
        f"cameras/{CAMERA_ID}/extra",
    ],
)
async def test_enabled_camera_from_path_rejects_malformed_paths(path):
    db = db_returning(make_camera())

    with pytest.raises(HTTPException) as exc:
        await _enabled_camera_from_path(path, db)

    assert exc.value.status_code == 401
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_enabled_camera_from_path_rejects_invalid_uuid():
    # Matches the 36-character pattern but is not a valid UUID.
    db = db_returning(make_camera())

    with pytest.raises(HTTPException) as exc:
        await _enabled_camera_from_path(f"cameras/{'-' * 36}", db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Path contains an invalid camera ID."
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_enabled_camera_from_path_rejects_missing_or_disabled_camera():
    db = db_returning(None)

    with pytest.raises(HTTPException) as exc:
        await _enabled_camera_from_path(CAMERA_PATH, db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Camera does not exist or is disabled."