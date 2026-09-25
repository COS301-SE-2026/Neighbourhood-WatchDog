import asyncio
import logging

from app.core.celery_app import celery
from app.core.database import WorkerSessionLocal
from app.services.dispatch_service import expire_stale_dispatchs

logger = logging.getLogger(__name__)

@celery.task
def expire_stale_dispatch_requests():
    asyncio.run(_expire_stale_dispatch_requests())

async def _expire_stale_dispatch_requests():
    async with WorkerSessionLocal() as db:
        try:
            expired = await expire_stale_dispatchs(db)
            if expired:
                logger.info("Expired %d stale dispatch request(s)", expired)
        except Exception:
            await db.rollback()
            logger.exception("Failed to expire stale dispatch requests")
