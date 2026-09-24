from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.tasks.incident_density_tasks import (
    _backfill_dates,
    backfill_incident_density,
    finalize_yesterday_incident_density,
    recompute_incident_density_day,
    refresh_current_incident_density,
)
from app.core.celery_app import celery


def run_task(task, *args):
    """
    Run the Celery task body directly without a worker.
    """
    return task.run(*args)


def test_refresh_current_density_rebuilds_today():
    target_date = date(2026, 9, 23)

    with patch(
        "app.tasks.incident_density_tasks._today",
        return_value=target_date,
    ), patch(
        "app.tasks.incident_density_tasks._rebuild_date",
        new=AsyncMock(),
    ) as rebuild:
        run_task(refresh_current_incident_density)

    rebuild.assert_awaited_once_with(target_date)


def test_finalize_yesterday_rebuilds_previous_day():
    today = date(2026, 9, 23)
    yesterday = date(2026, 9, 22)

    with patch(
        "app.tasks.incident_density_tasks._today",
        return_value=today,
    ), patch(
        "app.tasks.incident_density_tasks._rebuild_date",
        new=AsyncMock(),
    ) as rebuild:
        run_task(finalize_yesterday_incident_density)

    rebuild.assert_awaited_once_with(yesterday)


def test_recompute_task_parses_iso_date():
    with patch(
        "app.tasks.incident_density_tasks._rebuild_date",
        new=AsyncMock(),
    ) as rebuild:
        run_task(
            recompute_incident_density_day,
            "2026-09-20",
        )

    rebuild.assert_awaited_once_with(
        date(2026, 9, 20),
    )


def test_backfill_task_rebuilds_every_date_inclusive():
    with patch(
        "app.tasks.incident_density_tasks._rebuild_date",
        new=AsyncMock(),
    ) as rebuild:
        run_task(
            backfill_incident_density,
            "2026-09-20",
            "2026-09-22",
        )

    assert rebuild.await_count == 3
    assert [
        call.args[0]
        for call in rebuild.await_args_list
    ] == [
        date(2026, 9, 20),
        date(2026, 9, 21),
        date(2026, 9, 22),
    ]


def test_density_tasks_are_registered_in_beat_schedule():
    schedule = celery.conf.beat_schedule

    assert (
        "refresh-current-incident-density"
        in schedule
    )

    assert (
        "finalize-yesterday-incident-density"
        in schedule
    )

    assert (
        schedule["refresh-current-incident-density"]["task"]
        == (
            "app.tasks.incident_density_tasks."
            "refresh_current_incident_density"
        )
    )


@pytest.mark.asyncio
async def test_backfill_stops_when_rebuild_fails():
    error = RuntimeError("rebuild failed")

    with patch(
        "app.tasks.incident_density_tasks._rebuild_date",
        new=AsyncMock(side_effect=error),
    ) as rebuild:
        with pytest.raises(
            RuntimeError,
            match="rebuild failed",
        ):
            await _backfill_dates(
                date(2026, 9, 20),
                date(2026, 9, 22),
            )

    rebuild.assert_awaited_once_with(
        date(2026, 9, 20),
    )