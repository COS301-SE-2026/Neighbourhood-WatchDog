import asyncio
import base64
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select

from app.core.celery_app import celery
from app.core.database import worker_session
from app.models.alert import Alert
from app.models.tracking import TrackingSighting
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
        logger.warning(
            "Empty clip for alert %s; skipping upload",
            alert_id,
        )
        return

    if len(clip_bytes) > MAX_CLIP_SIZE_BYTES:
        raise ValueError(
            f"Invalid clip size for alert {alert_id}: "
            f"{len(clip_bytes)} bytes; maximum is "
            f"{MAX_CLIP_SIZE_BYTES} bytes"
        )

    async with worker_session() as db:
        alert_uuid = UUID(alert_id)
        stmt = select(Alert).where(Alert.id == alert_uuid)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if alert is None:
            logger.error("Alert %s not found when processing queued clip upload", alert_id)
            return

        if not S3_BUCKET_NAME:
            raise RuntimeError("S3 bucket is not configured")

        now = datetime.now(timezone.utc)

        # avoid uploading the same alert clip again while the existing S3 link is active
        existing_expires_at = alert.clip_expires_at

        if existing_expires_at is not None and existing_expires_at.tzinfo is None:
            existing_expires_at = existing_expires_at.replace(tzinfo=timezone.utc)

        if (alert.clip_s3_key and existing_expires_at is not None and existing_expires_at > now):
            logger.info("Alert %s already has an active clip; skipping duplicate upload", alert_id)
            return

        #frame_timestamp is stable for the alert, so retries generate the same S3 key
        timestamp = alert.frame_timestamp

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        s3_key = _clip_s3_key(alert, timestamp)
        expires_at = now + timedelta(days=CLIP_RETENTION_DAYS)

        await asyncio.to_thread(
            _s3_client().put_object,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=clip_bytes,
            ContentType=content_type or "video/mp4",
            ServerSideEncryption="AES256"
            
        )

        alert.clip_s3_key = s3_key
        alert.clip_expires_at = expires_at
        await db.commit()

        logger.info("Uploaded and linked clip for alert %s: s3://%s/%s", alert_id, S3_BUCKET_NAME, s3_key)


def _tracking_sighting_clip_s3_key(sighting: TrackingSighting, timestamp: datetime) -> str:
    return (
        f"clips/{sighting.camera_id}/{timestamp:%Y/%m/%d}/"
        f"tracking_{timestamp:%Y%m%dT%H%M%SZ}_{sighting.id}.mp4"
    )


@celery.task(bind=True, max_retries=5, acks_late=True)
def upload_tracking_sighting_clip_task(self, sighting_id: str, clip_b64: str, content_type: str) -> None:
    try:
        asyncio.run(
            _upload_tracking_sighting_clip(
                sighting_id,
                clip_b64,
                content_type
            )
        )

    except (BotoCoreError, ClientError) as exc:
        logger.warning("Transient S3 error for tracking sighting %s", sighting_id)
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 60))
    except Exception:
        logger.exception("Permanent failure uploading clip for tracking sighting %s", sighting_id)
        raise

async def _upload_tracking_sighting_clip(sighting_id: str, clip_b64: str, content_type: str) -> None:

    clip_bytes = base64.b64decode(clip_b64)

    if not clip_bytes or len(clip_bytes) > MAX_CLIP_SIZE_BYTES:
        logger.error("Invalid clip size for tracking sighting %s", sighting_id)
        return

    async with worker_session() as db:
        result = await db.execute(
            select(TrackingSighting)
            .where(TrackingSighting.id == UUID(sighting_id))
        )
        sighting = result.scalar_one_or_none()

        if sighting is None:
            logger.error("Tracking sighting %s not found", sighting_id)
            return

        timestamp = sighting.observed_at

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        s3_key = _tracking_sighting_clip_s3_key(sighting, timestamp)
        expires_at = datetime.now(timezone.utc) + timedelta(days=CLIP_RETENTION_DAYS)

        if (sighting.clip_s3_key and sighting.clip_expires_at and sighting.clip_expires_at > datetime.now(timezone.utc)):
            logger.info(
                "Tracking sighting %s already has an active clip; skipping duplicate upload", sighting_id)
            return


        if not S3_BUCKET_NAME:
            raise RuntimeError("S3 bucket is not configured")
        
        await asyncio.to_thread(
            
            _s3_client().put_object,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=clip_bytes,
            ContentType=content_type or "video/mp4",
            ServerSideEncryption="AES256"

        )

        sighting.clip_s3_key = s3_key
        sighting.clip_expires_at = expires_at

        await db.commit()

        logger.info("Uploaded and linked clip for tracking sighting %s", sighting_id)
