import asyncio
import base64
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select

from app.core.celery_app import celery
from app.core.database import SessionLocal, engine
from app.models.alert import Alert
from app.services.alert_service import CLIP_RETENTION_DAYS, S3_BUCKET_NAME, _clip_s3_key, _s3_client


logger = logging.getLogger(__name__)

MAX_CLIP_SIZE_BYTES = 5 * 1024 * 1024 # keeping it to 5MB since most clips seem to be under 1 MB anyways

@celery.task(bind=True, max_retries=5, acks_late=True)
def upload_alert_clip_task(self, alert_id: str, clip_b64: str, content_type: str) -> None:
    """ Runs in the Celery worker process. It will upload a clip to S3 bucket & link it to
    the alert. Retries with backoff on transient S3 errors"""

    try:
        asyncio.run(_upload_and_link(alert_id, clip_b64, content_type))
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Transient S3 error for alert %s (attempt %s). Retrying...", alert_id, self.request.retries)
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 60))
    except Exception:
        logger.exception("Permanent failure uploading clip for alert %s", alert_id)
        raise

async def _upload_and_link(alert_id: str, clip_b64: str, content_type: str) -> None:
    clip_bytes = base64.b64decode(clip_b64)

    if not clip_bytes:
        logger.error(
            "Clip for alert %s exceeds %s bytes (%s bytes). Skipping upload.",
            alert_id, MAX_CLIP_SIZE_BYTES, len(clip_bytes),
        )
        return

    async  with SessionLocal() as db:
        alert_uuid = UUID(alert_id)
        stmt = select(Alert).where(Alert.id == alert_uuid)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if alert is None:
            logger.error("Alert %s not found when processing queued clip upload", alert_id)
            return

        timestamp = datetime.now(timezone.utc)
        s3_key = _clip_s3_key(alert, timestamp)
        expires_at = timestamp + timedelta(days=CLIP_RETENTION_DAYS)

        await asyncio.to_thread(
            _s3_client().put_object,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=clip_bytes,
            ContentType=content_type or "video/mp4",
            ServerSideEncryption="AES256",
        )

        alert.clip_s3_key = s3_key
        alert.clip_expires_at = expires_at
        await db.commit()

        logger.info("Uploaded and linked clip for alert %s: s3://%s/%s", alert_id, S3_BUCKET_NAME, s3_key)