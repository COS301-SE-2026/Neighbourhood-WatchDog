from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.celery_app import celery
from app.tasks.danger_zone_tasks import (
    _recompute_all_danger_zones,
    _recompute_one_neighbourhood,
    recompute_neighbourhood_danger_zone,
)


def run_task(task, *args):
    return task.run(*args)


def test_manual_task_parses_identifiers_and_date():
    neighbourhood_id = uuid4()

    with patch(
        "app.tasks.danger_zone_tasks."
        "_recompute_one_neighbourhood",
        new=AsyncMock(return_value=3),
    ) as recompute:
        result = run_task(
            recompute_neighbourhood_danger_zone,
            str(neighbourhood_id),
            "2026-09-25",
        )

    assert result == 3
    recompute.assert_awaited_once_with(
        neighbourhood_id=neighbourhood_id,
        target_date=date(2026, 9, 25),
    )


@pytest.mark.asyncio
async def test_one_failure_does_not_stop_other_neighbourhoods():
    first_id = uuid4()
    second_id = uuid4()
    target_date = date(2026, 9, 25)

    with patch(
        "app.tasks.danger_zone_tasks."
        "_get_neighbourhood_ids",
        new=AsyncMock(
            return_value=[
                first_id,
                second_id,
            ]
        ),
    ), patch(
        "app.tasks.danger_zone_tasks."
        "_recompute_one_neighbourhood",
        new=AsyncMock(
            side_effect=[
                RuntimeError("failed"),
                2,
            ]
        ),
    ) as recompute:
        result = (
            await _recompute_all_danger_zones(
                target_date
            )
        )

    assert result == {
        "completed": 1,
        "failed": 1,
    }
    assert recompute.await_count == 2


@pytest.mark.asyncio
async def test_failed_neighbourhood_is_rolled_back():
    neighbourhood_id = uuid4()
    target_date = date(2026, 9, 25)

    db = MagicMock()
    db.rollback = AsyncMock()

    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(
        return_value=db
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None
    )

    with patch(
        "app.tasks.danger_zone_tasks."
        "WorkerSessionLocal",
        return_value=session_context,
    ), patch(
        "app.tasks.danger_zone_tasks."
        "rebuild_neighbourhood_danger_zone",
        new=AsyncMock(
            side_effect=RuntimeError(
                "calculation failed"
            )
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="calculation failed",
        ):
            await _recompute_one_neighbourhood(
                neighbourhood_id,
                target_date,
            )

    db.rollback.assert_awaited_once()


def test_danger_zone_task_is_scheduled():
    schedule = celery.conf.beat_schedule

    assert (
        "recompute-danger-zones-every-10-minutes"
        in schedule
    )

    assert (
        schedule[
            "recompute-danger-zones-every-10-minutes"
        ]["task"]
        == (
            "app.tasks.danger_zone_tasks."
            "recompute_all_danger_zones"
        )
    )
