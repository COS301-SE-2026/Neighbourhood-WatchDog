import asyncio
import logging
from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.celery_app import celery
from app.core.database import WorkerSessionLocal
from app.models.neighbourhood import Neighbourhood
from app.services.danger_zone_service import (
    rebuild_neighbourhood_danger_zone,
)


logger = logging.getLogger(__name__)

LOCAL_TIMEZONE = ZoneInfo(
    "Africa/Johannesburg"
)


def _today() -> date:
    return datetime.now(
        LOCAL_TIMEZONE
    ).date()


def _parse_date(
    value: str | None,
) -> date:
    return (
        date.fromisoformat(value)
        if value is not None
        else _today()
    )


@celery.task
def recompute_all_danger_zones(
    target_date: str | None = None,
):
    return asyncio.run(
        _recompute_all_danger_zones(
            _parse_date(target_date)
        )
    )


@celery.task
def recompute_neighbourhood_danger_zone(
    neighbourhood_id: str,
    target_date: str | None = None,
):
    return asyncio.run(
        _recompute_one_neighbourhood(
            neighbourhood_id=UUID(
                neighbourhood_id
            ),
            target_date=_parse_date(
                target_date
            ),
        )
    )


@celery.task
def backfill_danger_zones(
    start_date: str,
    end_date: str,
):
    return asyncio.run(
        _backfill_danger_zones(
            start_date=date.fromisoformat(
                start_date
            ),
            end_date=date.fromisoformat(
                end_date
            ),
        )
    )


async def _get_neighbourhood_ids() -> list[UUID]:
    async with WorkerSessionLocal() as db:
        result = await db.execute(
            select(Neighbourhood.id)
        )

        return list(
            result.scalars().all()
        )


async def _recompute_one_neighbourhood(
    neighbourhood_id: UUID,
    target_date: date,
) -> int:
    async with WorkerSessionLocal() as db:
        try:
            return (
                await rebuild_neighbourhood_danger_zone(
                    neighbourhood_id=(
                        neighbourhood_id
                    ),
                    target_date=target_date,
                    db=db,
                )
            )
        except Exception:
            await db.rollback()
            logger.exception(
                "Failed to rebuild danger zone "
                "for neighbourhood=%s "
                "target_date=%s",
                neighbourhood_id,
                target_date,
            )
            raise


async def _recompute_all_danger_zones(
    target_date: date,
) -> dict[str, int]:
    neighbourhood_ids = (
        await _get_neighbourhood_ids()
    )

    completed = 0
    failed = 0

    for neighbourhood_id in neighbourhood_ids:
        try:
            await _recompute_one_neighbourhood(
                neighbourhood_id=(
                    neighbourhood_id
                ),
                target_date=target_date,
            )
            completed += 1
        except Exception:
            # The individual neighbourhood transaction
            # has already been rolled back and logged.
            failed += 1

    return {
        "completed": completed,
        "failed": failed,
    }


async def _backfill_danger_zones(
    start_date: date,
    end_date: date,
) -> dict[str, int]:
    if start_date > end_date:
        raise ValueError(
            "start_date must not be after end_date"
        )

    completed = 0
    failed = 0
    current_date = start_date

    while current_date <= end_date:
        result = (
            await _recompute_all_danger_zones(
                current_date
            )
        )
        completed += result["completed"]
        failed += result["failed"]
        current_date += timedelta(days=1)

    return {
        "completed": completed,
        "failed": failed,
    }
