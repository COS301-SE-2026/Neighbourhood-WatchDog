import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.core.celery_app import celery
from app.core.database import WorkerSessionLocal
from app.models.neighbourhood import Neighbourhood
from app.services.risk_score_service import calculate_risk_score_handler


logger = logging.getLogger(__name__)


@celery.task
def recalculate_all_risk_scores():
    asyncio.run(_recalculate_all_risk_scores())


async def _recalculate_all_risk_scores():
    async with WorkerSessionLocal() as db:
        result = await db.execute(select(Neighbourhood.id))
        neighbourhood_ids = result.scalars().all()

    for neighbourhood_id in neighbourhood_ids:
        calculate_risk_score_task.delay(str(neighbourhood_id))



@celery.task
def calculate_risk_score_task(neighbourhood_id: str):
    asyncio.run(_calculate_risk_score_task(neighbourhood_id))

async def _calculate_risk_score_task(neighbourhood_id: str):
    async with WorkerSessionLocal() as db:
        try:
            await calculate_risk_score_handler(UUID(neighbourhood_id), db)

        except Exception:
            await db.rollback()
            logger.exception("Failed to calculate risk score for neighbourhood %s", neighbourhood_id)
