import asyncio
import base64
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from botocore.exceptions import BotoCoreError, ClientError

from app.tasks import clip_tasks as service


ALERT_ID = str(uuid.uuid4())


def make_session(alert):
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = alert
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=False)
    return db, session_context


def make_alert():
    return SimpleNamespace(
        id=uuid.UUID(ALERT_ID),
        clip_s3_key=None,
        clip_expires_at=None,
    )


class TestUploadAndLink:
    @pytest.mark.asyncio
    async def test_empty_clip_is_skipped_before_database_access(self):
        with patch.object(service, "WorkerSessionLocal") as session_factory:
            await service._upload_and_link(ALERT_ID, "", "video/mp4")

        session_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_alert_is_skipped_without_s3_upload(self):
        db, session_context = make_session(None)
        s3_client = Mock()

        with (
            patch.object(service, "WorkerSessionLocal", return_value=session_context),
            patch.object(service, "_s3_client", return_value=s3_client),
        ):
            await service._upload_and_link(
                ALERT_ID,
                base64.b64encode(b"clip-data").decode(),
                "video/mp4",
            )

        db.commit.assert_not_awaited()
        s3_client.put_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_uploads_clip_links_alert_and_defaults_content_type(self):
        alert = make_alert()
        db, session_context = make_session(alert)
        s3_client = Mock()
        to_thread = AsyncMock()
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with (
            patch.object(service, "WorkerSessionLocal", return_value=session_context),
            patch.object(service, "_s3_client", return_value=s3_client),
            patch.object(service, "_clip_s3_key", return_value="clips/test.mp4"),
            patch.object(service, "datetime") as datetime_module,
            patch.object(service.asyncio, "to_thread", new=to_thread),
        ):
            datetime_module.now.return_value = timestamp
            await service._upload_and_link(
                ALERT_ID,
                base64.b64encode(b"clip-data").decode(),
                "",
            )

        to_thread.assert_awaited_once()
        assert to_thread.await_args.args[0] is s3_client.put_object
        assert to_thread.await_args.kwargs == {
            "Bucket": service.S3_BUCKET_NAME,
            "Key": "clips/test.mp4",
            "Body": b"clip-data",
            "ContentType": "video/mp4",
            "ServerSideEncryption": "AES256",
        }
        assert alert.clip_s3_key == "clips/test.mp4"
        assert alert.clip_expires_at == timestamp + timedelta(days=service.CLIP_RETENTION_DAYS)
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_preserves_explicit_content_type(self):
        alert = make_alert()
        db, session_context = make_session(alert)
        s3_client = Mock()
        to_thread = AsyncMock()

        with (
            patch.object(service, "WorkerSessionLocal", return_value=session_context),
            patch.object(service, "_s3_client", return_value=s3_client),
            patch.object(service, "_clip_s3_key", return_value="clips/test.webm"),
            patch.object(service.asyncio, "to_thread", new=to_thread),
        ):
            await service._upload_and_link(
                ALERT_ID,
                base64.b64encode(b"clip-data").decode(),
                "video/webm",
            )

        assert to_thread.await_args.kwargs["ContentType"] == "video/webm"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_alert_id_raises_before_commit(self):
        db, session_context = make_session(make_alert())

        with patch.object(service, "WorkerSessionLocal", return_value=session_context):
            with pytest.raises(ValueError):
                await service._upload_and_link(
                    "not-a-uuid",
                    base64.b64encode(b"clip-data").decode(),
                    "video/mp4",
                )

        db.commit.assert_not_awaited()


class RetrySignal(Exception):
    pass


def run_and_raise(error):
    def runner(coroutine):
        coroutine.close()
        raise error
    return runner


class TestUploadAlertClipTask:
    def test_retries_on_botocore_error(self):
        error = BotoCoreError(error_msg="temporary S3 error")
        with (
            patch.object(service.asyncio, "run", side_effect=run_and_raise(error)),
            patch.object(
                service.upload_alert_clip_task,
                "retry",
                side_effect=RetrySignal,
            ) as retry,
        ):
            with pytest.raises(RetrySignal):
                service.upload_alert_clip_task.run(ALERT_ID, "Y2xpcA==", "video/mp4")

        retry.assert_called_once_with(exc=error, countdown=1)

    def test_reraises_permanent_failure(self):
        error = ValueError("invalid clip payload")
        with patch.object(service.asyncio, "run", side_effect=run_and_raise(error)):
            with pytest.raises(ValueError, match="invalid clip payload"):
                service.upload_alert_clip_task.run(ALERT_ID, "not-base64", "video/mp4")