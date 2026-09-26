from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.danger_zone import DangerZoneQuery
from app.services.camera_coverage_grid import (
    web_mercator_to_wgs84,
)
from app.services.danger_zone_query_service import (
    get_danger_zones_handler,
)


def make_filters() -> DangerZoneQuery:
    return DangerZoneQuery(
        west=28.20,
        south=-25.80,
        east=28.30,
        north=-25.70,
    )


def make_row(
    *,
    grid_x: int = 3142700,
    grid_y: int = -2963800,
    danger_score: float = 0.75,
):
    return SimpleNamespace(
        grid_x=grid_x,
        grid_y=grid_y,
        cell_size_metres=100,
        latitude=-25.75,
        longitude=28.23,
        incident_count=10,
        incident_score=1.0,
        coverage_ratio=0.25,
        coverage_sparsity=0.75,
        danger_score=danger_score,
        window_start=date(2026, 8, 27),
        window_end=date(2026, 9, 25),
        calculated_at=datetime(
            2026,
            9,
            25,
            14,
            0,
            tzinfo=timezone.utc,
        ),
    )


@pytest.mark.asyncio
async def test_requires_authentication():
    db = MagicMock()

    with pytest.raises(HTTPException) as error:
        await get_danger_zones_handler(
            neighbourhood_id=uuid4(),
            filters=make_filters(),
            db=db,
            claims={},
        )

    assert error.value.status_code == 401
    db.scalar.assert_not_called()


@pytest.mark.asyncio
async def test_returns_empty_when_no_cached_snapshot_exists():
    db = MagicMock()
    db.scalar = AsyncMock(return_value=None)

    result = await get_danger_zones_handler(
        neighbourhood_id=uuid4(),
        filters=make_filters(),
        db=db,
        claims={"sub": "member-sub"},
    )

    assert result.cells == []
    assert result.min_score == 0.0
    assert result.max_score == 0.0
    assert result.calculated_at is None
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_returns_empty_when_snapshot_has_no_cells_in_viewport():
    neighbourhood_id = uuid4()
    window_end = date(2026, 9, 25)

    db = MagicMock()
    db.scalar = AsyncMock(return_value=window_end)

    query_result = MagicMock()
    query_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=query_result)

    result = await get_danger_zones_handler(
        neighbourhood_id=neighbourhood_id,
        filters=make_filters(),
        db=db,
        claims={"sub": "member-sub"},
    )

    assert result.neighbourhood_id == neighbourhood_id
    assert result.cells == []
    assert result.window_end == window_end
    assert result.min_score == 0.0
    assert result.max_score == 0.0


@pytest.mark.asyncio
async def test_returns_latest_snapshot_cells_and_rectangle_bounds():
    neighbourhood_id = uuid4()
    row = make_row(danger_score=0.75)

    db = MagicMock()
    db.scalar = AsyncMock(
        return_value=date(2026, 9, 25),
    )

    query_result = MagicMock()
    query_result.scalars.return_value.all.return_value = [
        row,
    ]
    db.execute = AsyncMock(return_value=query_result)

    result = await get_danger_zones_handler(
        neighbourhood_id=neighbourhood_id,
        filters=make_filters(),
        db=db,
        claims={"sub": "member-sub"},
    )

    assert result.neighbourhood_id == neighbourhood_id
    assert result.window_start == date(2026, 8, 27)
    assert result.window_end == date(2026, 9, 25)
    assert result.cell_size_metres == 100
    assert result.min_score == 0.75
    assert result.max_score == 0.75
    assert len(result.cells) == 1

    cell = result.cells[0]

    assert cell.cell_id == "3142700:-2963800"
    assert cell.grid_x == 3142700
    assert cell.grid_y == -2963800
    assert cell.danger_score == 0.75
    assert cell.coverage_ratio == 0.25
    assert cell.coverage_sparsity == 0.75

    expected_south, expected_west = (
        web_mercator_to_wgs84(
            row.grid_x,
            row.grid_y,
        )
    )

    expected_north, expected_east = (
        web_mercator_to_wgs84(
            row.grid_x + row.cell_size_metres,
            row.grid_y + row.cell_size_metres,
        )
    )

    assert cell.south == pytest.approx(
        expected_south,
    )
    assert cell.west == pytest.approx(
        expected_west,
    )
    assert cell.north == pytest.approx(
        expected_north,
    )
    assert cell.east == pytest.approx(
        expected_east,
    )


@pytest.mark.asyncio
async def test_database_failure_becomes_http_500():
    db = MagicMock()
    db.scalar = AsyncMock(
        side_effect=RuntimeError("database unavailable"),
    )

    with pytest.raises(HTTPException) as error:
        await get_danger_zones_handler(
            neighbourhood_id=uuid4(),
            filters=make_filters(),
            db=db,
            claims={"sub": "member-sub"},
        )

    assert error.value.status_code == 500
    assert error.value.detail == (
        "Failed to retrieve danger zones"
    )