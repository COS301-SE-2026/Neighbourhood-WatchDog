"""This file deals with the sending of push notifications using the redis queue"""

import asyncio
import logging
from uuid import UUID

from firebase_admin import messaging
from sqlalchemy import select

from app.core.celery_app import celery
from app.core.database import WorkerSessionLocal
from app.models.push_device import PushDevice

logger = logging.getLogger(__name__)

@celery.task(bind=True, acks_late=True)
def send_push_to_users(
    user_ids: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None,
) -> None:
    try: 
        asyncio.run(_send_to_users(user_ids, title, body, data))
    except Exception:
        logger.exception("Permanent failure sending push to users %s", user_ids)
        raise

async def _send_to_users(
    user_ids: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None,
) -> None:
    if not user_ids:
        return

    user_uuids = [UUID(u) for u in user_ids]

    async with WorkerSessionLocal() as db:
        stmt = select(PushDevice).where(PushDevice.user_id.in_(user_uuids))
        result = await db.execute(stmt)
        devices = result.scalars().all()

        stale_device_ids = []

        for device in devices:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=device.device_token,
            )
            try:
                await asyncio.to_thread(messaging.send, message)
            except messaging.UnregisteredError:
                stale_device_ids.append(device.id)
            except Exception:
                logger.exception("send_push_to_users: failed to send push to device_id=%s", device.id)

        if stale_device_ids:
            del_stmt = PushDevice.__table__.delete().where(
                PushDevice.id.in_(stale_device_ids)
            )
            await db.execute(del_stmt)

        await db.commit()
        logger.info(
            "send_push_to_users: sent to %s devices(s) for %s user(s), pruned %s stale token(s)",
            len(devices), len(user_ids), len(stale_device_ids),
        )