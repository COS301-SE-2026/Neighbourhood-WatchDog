"""Celery tasks for the email and whatsapp notifications"""

import asyncio
import logging
from uuid import UUID

from app.core.celery_app import celery
from app.core.database import worker_session
from app.models.notification import Notification, NotificationChannelEnum, NotificationStatus
from app.services.notifications.notification_service import send_email_smtp, send_email_bcc_smtp, send_whatsapp

from app.schemas.notification import EventType

logger = logging.getLogger(__name__)

# EMAIL TASK

@celery.task(acks_late=True)
def send_email_task(
    source_id: str | None,
    user_id: str,
    recipient_email: str,
    subject: str,
    html_body: str,
    plain_body: str,
) -> None:
    try: 
        asyncio.run(_send_and_log_email(
            source_id,
            user_id,
            recipient_email,
            subject,
            html_body,
            plain_body,
        ))
    except Exception:
        logger.exception("Permanent failure sending email to %s", recipient_email)
        raise

async def _send_and_log_email(
    source_id,
    user_id,
    recipient_email,
    subject,
    html_body,
    plain_body,
) -> None:
    success, error = await asyncio.to_thread(send_email_smtp, recipient_email, subject, html_body, plain_body)

    async with worker_session() as db:
        db.add(Notification(
            alert_id=UUID(source_id) if source_id else None,
            user_id=UUID(user_id),
            channel=NotificationChannelEnum.EMAIL,
            status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
            error_message=error,
        ))
        await db.commit()

@celery.task(acks_late=True)
def send_email_bcc_task(
    source_id: str | None,
    user_id: str,
    recipient_emails: list[str],
    subject: str,
    html_body: str,
    plain_body: str,
) -> None:
    try: 
        asyncio.run(_send_and_log_email_bcc(
            source_id,
            user_id,
            recipient_emails,
            subject,
            html_body,
            plain_body,
        ))
    except Exception:
        logger.exception("Permanent failure sending email to %s", len(recipient_emails))
        raise

async def _send_and_log_email_bcc(
    source_id,
    user_id,
    recipient_emails,
    subject,
    html_body,
    plain_body,
) -> None:
    success, error = await asyncio.to_thread(send_email_bcc_smtp, recipient_emails, subject, html_body, plain_body)

    async with worker_session() as db:
        db.add(Notification(
            alert_id=UUID(source_id) if source_id else None,
            user_id=UUID(user_id),
            channel=NotificationChannelEnum.EMAIL,
            status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
            error_message=error,
        ))
        await db.commit()


# WHATSAPP TASK

@celery.task(acks_late=True)
def send_whatsapp_task(
    source_id: str | None,
    user_id: str,
    phone_number: str,
    message: str,
) -> None:
    try: 
        asyncio.run(_send_and_log_whatsapp(
            source_id,
            user_id,
            phone_number,
            message,
        ))
    except Exception:
        logger.exception("Permanent failure sending WhatsApp to %s", phone_number)
        raise

async def _send_and_log_whatsapp(
    source_id: str | None,
    user_id: str,
    phone_number: str,
    message: str,
) -> None:
    success, error = await asyncio.to_thread(send_whatsapp, phone_number, message)

    async with worker_session() as db:
        db.add(Notification(
            alert_id=UUID(source_id) if source_id else None,
            user_id=UUID(user_id),
            channel=NotificationChannelEnum.WHATSAPP,
            status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
            error_message=error,
        ))
        await db.commit()