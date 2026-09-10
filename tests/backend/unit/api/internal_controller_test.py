import base64
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.internal import (
    create_alert,
    update_clip,
    upload_clip,
)
from app.schemas.alert import (
    AlertClipUpdateRes,
    ClipUploadAcceptedRes,
    CreateInternalAlertRequest,
    InternalAlertCreateRes,
    UpdateAlertClipRequest,
)
from app.tasks.clip_tasks import MAX_CLIP_SIZE_BYTES


ALERT_ID = uuid4()
CAMERA_ID = uuid4()
PROPERTY_ID = uuid4()

DB = Mock()
CREDENTIAL = Mock(property_id=PROPERTY_ID)


def make_create_alert_request():
    return CreateInternalAlertRequest(
        camera_id=str(CAMERA_ID),
        detection_type="HUMAN_PRESENCE",
        confidence_score=0.91,
        thumbnail_url="https://example.com/thumbnail.jpg",
        frame_timestamp="2026-01-01T12:00:00+00:00",
    )


def make_update_clip_request():
    return UpdateAlertClipRequest(
        clip_s3_key="clips/example.mp4",
        clip_expires_at="2026-01-08T12:00:00+00:00",
    )


@pytest.mark.asyncio
async def test_create_alert_delegates_to_service():
    body = make_create_alert_request()
    expected_response = InternalAlertCreateRes(
        alert_id=ALERT_ID,
    )

    with patch(
        "app.api.controllers.internal.create_alert_for_agent_handler",
        new=AsyncMock(return_value=expected_response),
    ) as handler:
        response = await create_alert(
            body=body,
            db=DB,
            credential=CREDENTIAL,
        )

    assert response == expected_response

    handler.assert_awaited_once_with(
        body=body,
        credential=CREDENTIAL,
        db=DB,
    )


@pytest.mark.asyncio
async def test_create_alert_propagates_service_error():
    body = make_create_alert_request()
    error = HTTPException(
        status_code=404,
        detail="Camera not found",
    )

    with patch(
        "app.api.controllers.internal.create_alert_for_agent_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await create_alert(
                body=body,
                db=DB,
                credential=CREDENTIAL,
            )

    assert exc_info.value is error

    handler.assert_awaited_once_with(
        body=body,
        credential=CREDENTIAL,
        db=DB,
    )


@pytest.mark.asyncio
async def test_update_clip_delegates_to_service():
    body = make_update_clip_request()
    expected_response = AlertClipUpdateRes(
        alert_id=ALERT_ID,
        clip_s3_key="clips/example.mp4",
        clip_expires_at=datetime(
            2026,
            1,
            8,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    with patch(
        "app.api.controllers.internal.update_alert_clip_for_agent_handler",
        new=AsyncMock(return_value=expected_response),
    ) as handler:
        response = await update_clip(
            alert_id=str(ALERT_ID),
            body=body,
            db=DB,
            credential=CREDENTIAL,
        )

    assert response == expected_response

    handler.assert_awaited_once_with(
        alert_id=str(ALERT_ID),
        body=body,
        credential=CREDENTIAL,
        db=DB,
    )


@pytest.mark.asyncio
async def test_update_clip_propagates_service_error():
    body = make_update_clip_request()
    error = HTTPException(
        status_code=404,
        detail="Alert not found",
    )

    with patch(
        "app.api.controllers.internal.update_alert_clip_for_agent_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await update_clip(
                alert_id=str(ALERT_ID),
                body=body,
                db=DB,
                credential=CREDENTIAL,
            )

    assert exc_info.value is error

    handler.assert_awaited_once_with(
        alert_id=str(ALERT_ID),
        body=body,
        credential=CREDENTIAL,
        db=DB,
    )


@pytest.mark.asyncio
async def test_upload_clip_rejects_unsupported_content_type():
    clip = Mock()
    clip.content_type = "text/plain"

    with patch(
        "app.api.controllers.internal._read_clip_with_limit",
        new=AsyncMock(),
    ) as read_clip:
        with pytest.raises(HTTPException) as exc_info:
            await upload_clip(
                alert_id=str(ALERT_ID),
                db=DB,
                credential=CREDENTIAL,
                clip=clip,
            )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "Clip upload must use video/mp4 content type"
    )
    read_clip.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_clip_accepts_application_octet_stream():
    clip = Mock()
    clip.content_type = "application/octet-stream"

    clip_bytes = b"binary-clip-data"
    alert = SimpleNamespace(id=ALERT_ID)

    with (
        patch(
            "app.api.controllers.internal._read_clip_with_limit",
            new=AsyncMock(return_value=clip_bytes),
        ) as read_clip,
        patch(
            "app.api.controllers.internal.get_alert_for_agent",
            new=AsyncMock(return_value=alert),
        ) as get_alert,
        patch(
            "app.api.controllers.internal.upload_alert_clip_task.delay",
        ) as delay,
    ):
        response = await upload_clip(
            alert_id=str(ALERT_ID),
            db=DB,
            credential=CREDENTIAL,
            clip=clip,
        )

    assert isinstance(response, ClipUploadAcceptedRes)
    assert response.alert_id == ALERT_ID
    assert response.status == "queued"

    read_clip.assert_awaited_once_with(
        clip,
        MAX_CLIP_SIZE_BYTES,
    )

    get_alert.assert_awaited_once_with(
        str(ALERT_ID),
        CREDENTIAL,
        DB,
    )

    delay.assert_called_once_with(
        str(ALERT_ID),
        base64.b64encode(clip_bytes).decode("ascii"),
        "application/octet-stream",
    )


@pytest.mark.asyncio
async def test_upload_clip_rejects_empty_upload():
    clip = Mock()
    clip.content_type = "video/mp4"

    with (
        patch(
            "app.api.controllers.internal._read_clip_with_limit",
            new=AsyncMock(return_value=b""),
        ) as read_clip,
        patch(
            "app.api.controllers.internal.get_alert_for_agent",
            new=AsyncMock(),
        ) as get_alert,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await upload_clip(
                alert_id=str(ALERT_ID),
                db=DB,
                credential=CREDENTIAL,
                clip=clip,
            )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The uploaded clip is empty"

    read_clip.assert_awaited_once_with(
        clip,
        MAX_CLIP_SIZE_BYTES,
    )
    get_alert.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_clip_rejects_when_alert_does_not_exist():
    clip = Mock()
    clip.content_type = "video/mp4"

    with (
        patch(
            "app.api.controllers.internal._read_clip_with_limit",
            new=AsyncMock(return_value=b"clip-data"),
        ),
        patch(
            "app.api.controllers.internal.get_alert_for_agent",
            new=AsyncMock(return_value=None),
        ) as get_alert,
        patch(
            "app.api.controllers.internal.upload_alert_clip_task.delay",
        ) as delay,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await upload_clip(
                alert_id=str(ALERT_ID),
                db=DB,
                credential=CREDENTIAL,
                clip=clip,
            )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Alert not found"

    get_alert.assert_awaited_once_with(
        str(ALERT_ID),
        CREDENTIAL,
        DB,
    )
    delay.assert_not_called()


@pytest.mark.asyncio
async def test_upload_clip_rejects_clip_larger_than_limit():
    clip = Mock()
    clip.content_type = "video/mp4"

    error = HTTPException(
        status_code=413,
        detail="Clip exceeds upload limit",
    )

    with (
        patch(
            "app.api.controllers.internal._read_clip_with_limit",
            new=AsyncMock(side_effect=error),
        ) as read_clip,
        patch(
            "app.api.controllers.internal.get_alert_for_agent",
            new=AsyncMock(),
        ) as get_alert,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await upload_clip(
                alert_id=str(ALERT_ID),
                db=DB,
                credential=CREDENTIAL,
                clip=clip,
            )

    assert exc_info.value is error
    assert exc_info.value.status_code == 413

    read_clip.assert_awaited_once_with(
        clip,
        MAX_CLIP_SIZE_BYTES,
    )
    get_alert.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_clip_encodes_clip_and_queues_upload_task():
    clip = Mock()
    clip.content_type = "video/mp4"

    clip_bytes = b"test-video-content"
    alert = SimpleNamespace(id=ALERT_ID)

    with (
        patch(
            "app.api.controllers.internal._read_clip_with_limit",
            new=AsyncMock(return_value=clip_bytes),
        ) as read_clip,
        patch(
            "app.api.controllers.internal.get_alert_for_agent",
            new=AsyncMock(return_value=alert),
        ) as get_alert,
        patch(
            "app.api.controllers.internal.upload_alert_clip_task.delay",
        ) as delay,
    ):
        response = await upload_clip(
            alert_id=str(ALERT_ID),
            db=DB,
            credential=CREDENTIAL,
            clip=clip,
        )

    expected_base64 = base64.b64encode(clip_bytes).decode("ascii")

    assert response.alert_id == ALERT_ID
    assert response.status == "queued"

    read_clip.assert_awaited_once_with(
        clip,
        MAX_CLIP_SIZE_BYTES,
    )

    get_alert.assert_awaited_once_with(
        str(ALERT_ID),
        CREDENTIAL,
        DB,
    )

    delay.assert_called_once_with(
        str(ALERT_ID),
        expected_base64,
        "video/mp4",
    )