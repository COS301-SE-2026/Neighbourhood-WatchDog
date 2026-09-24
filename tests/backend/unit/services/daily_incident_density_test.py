from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import literal_column

from app.services.daily_incident_density_service import (
    _utc_day_bounds,
    rebuild_incident_density_day,
)


TARGET_DATE = date(2026, 9, 1)


def make_query_result(rows):
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    return result


def make_grid_expressions():
    return (
        literal_column("1"),
        literal_column("2"),
        literal_column("3"),
        literal_column("4"),
    )


@pytest.mark.asyncio
async def test_utc_day_bounds_use_south_african_midnight():
    start_at, end_at = _utc_day_bounds(TARGET_DATE)

    assert start_at == datetime(
        2026,
        8,
        31,
        22,
        0,
        tzinfo=timezone.utc,
    )

    assert end_at == datetime(
        2026,
        9,
        1,
        22,
        0,
        tzinfo=timezone.utc,
    )


@pytest.mark.asyncio
async def test_rebuild_adds_density_rows_and_commits():
    neighbourhood_id = uuid4()

    rows = [
        {
            "neighbourhood_id": neighbourhood_id,
            "grid_x": 100,
            "grid_y": 200,
            "latitude": -25.747,
            "longitude": 28.229,
            "incident_count": 4,
        },
        {
            "neighbourhood_id": neighbourhood_id,
            "grid_x": 101,
            "grid_y": 200,
            "latitude": -25.748,
            "longitude": 28.230,
            "incident_count": 7,
        },
    ]

    db = AsyncMock()
    db.execute.side_effect = [
        make_query_result(rows),
        MagicMock(),
    ]

    with patch(
        "app.services.daily_incident_density_service."
        "incident_grid_expressions",
        return_value=make_grid_expressions(),
    ):
        count = await rebuild_incident_density_day(
            TARGET_DATE,
            db,
        )

    assert count == 2
    assert db.execute.await_count == 2
    db.add_all.assert_called_once()
    db.commit.assert_awaited_once()

    inserted_rows = db.add_all.call_args.args[0]

    assert len(inserted_rows) == 2

    first = inserted_rows[0]
    assert first.neighbourhood_id == neighbourhood_id
    assert first.incident_date == TARGET_DATE
    assert first.cell_size_metres == 100
    assert first.grid_x == 100
    assert first.grid_y == 200
    assert first.latitude == -25.747
    assert first.longitude == 28.229
    assert first.incident_count == 4


@pytest.mark.asyncio
async def test_rebuild_is_idempotent_for_empty_results():
    db = AsyncMock()
    db.execute.side_effect = [
        make_query_result([]),
        MagicMock(),
    ]

    with patch(
        "app.services.daily_incident_density_service."
        "incident_grid_expressions",
        return_value=make_grid_expressions(),
    ):
        count = await rebuild_incident_density_day(
            TARGET_DATE,
            db,
        )

    assert count == 0
    db.add_all.assert_called_once_with([])
    db.commit.assert_awaited_once()
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_rebuild_deletes_existing_rows_for_target_date():
    db = AsyncMock()
    db.execute.side_effect = [
        make_query_result([]),
        MagicMock(),
    ]

    with patch(
        "app.services.daily_incident_density_service."
        "incident_grid_expressions",
        return_value=make_grid_expressions(),
    ):
        await rebuild_incident_density_day(
            TARGET_DATE,
            db,
        )

    delete_statement = db.execute.await_args_list[1].args[0]
    statement_text = str(delete_statement)

    assert "daily_incident_density" in statement_text
    assert "incident_date" in statement_text


@pytest.mark.asyncio
async def test_rebuild_propagates_database_errors():
    db = AsyncMock()
    db.execute.side_effect = RuntimeError(
        "database unavailable",
    )

    with patch(
        "app.services.daily_incident_density_service."
        "incident_grid_expressions",
        return_value=make_grid_expressions(),
    ):
        with pytest.raises(
            RuntimeError,
            match="database unavailable",
        ):
            await rebuild_incident_density_day(
                TARGET_DATE,
                db,
            )

    db.commit.assert_not_awaited()