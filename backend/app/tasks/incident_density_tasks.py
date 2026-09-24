import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.celery_app import celery
from app.core.database import WorkerSessionLocal
from app.services.daily_incident_density_service import (
    rebuild_incident_density_day
)


logger = logging.getLogger(__name__)

LOCAL_TIMEZONE = ZoneInfo("Africa/Johannesburg")


def _today() -> date:
    return datetime.now(
        LOCAL_TIMEZONE
    ).date()


@celery.task
def refresh_current_incident_density():
    asyncio.run(_rebuild_date(_today()))


@celery.task
def finalize_yesterday_incident_density():
    target_date = _today() - timedelta(days=1)

    asyncio.run(_rebuild_date(target_date))


@celery.task
def recompute_incident_density_day(
    target_date: str,
):
    asyncio.run(
        _rebuild_date(
            date.fromisoformat(target_date)
        )
    )


@celery.task
def backfill_incident_density(
    start_date: str,
    end_date: str,
):
    asyncio.run(
        _backfill_dates(
            date.fromisoformat(start_date),
            date.fromisoformat(end_date),
        )
    )


async def _rebuild_date(
    target_date: date,
) -> None:
    async with WorkerSessionLocal() as db:
        try:
            await rebuild_incident_density_day(
                target_date,
                db,
            )
        except Exception:
            await db.rollback()
            logger.exception(
                "Failed to rebuild incident "
                "density for date=%s",
                target_date,
            )
            raise


async def _backfill_dates(
    start_date: date,
    end_date: date,
) -> None:
    current_date = start_date

    while current_date <= end_date:
        await _rebuild_date(current_date)
        current_date += timedelta(days=1)
