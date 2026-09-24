from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.alert import IncidentDensityQuery
from app.services.incident_density_service import (
    get_incident_density_handler,
)


NEIGHBOURHOOD_ID = uuid4()


def make_filters():
    return IncidentDensityQuery(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 23),
        west=28.20,
        south=-25.80,
        east=28.30,
        north=-25.70,
    )


def make_db(rows):
    db = AsyncMock()

    result = MagicMock()
    result.mappings.return_value.all.return_value = rows

    db.execute.return_value = result
    return db


@pytest.mark.asyncio
async def test_requires_authentication():
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_incident_density_handler(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            filters=make_filters(),
            db=db,
            claims=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_returns_cells_and_normalises_counts():
    rows = [
        {
            "grid_x": 100,
            "grid_y": 200,
            "latitude": -25.747,
            "longitude": 28.229,
            "incident_count": 3,
        },
        {
            "grid_x": 101,
            "grid_y": 200,
            "latitude": -25.748,
            "longitude": 28.230,
            "incident_count": 8,
        },
    ]

    db = make_db(rows)

    result = await get_incident_density_handler(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        filters=make_filters(),
        db=db,
        claims={"id": str(uuid4())},
    )

    assert result.neighbourhood_id == NEIGHBOURHOOD_ID
    assert result.start_date == date(2026, 9, 1)
    assert result.end_date == date(2026, 9, 23)
    assert result.cell_size_metres == 100

    assert result.min_count == 3
    assert result.max_count == 8
    assert len(result.cells) == 2

    assert result.cells[0].cell_id == "100:200"
    assert result.cells[0].incident_count == 3
    assert result.cells[1].cell_id == "101:200"
    assert result.cells[1].incident_count == 8


@pytest.mark.asyncio
async def test_returns_empty_density_data():
    db = make_db([])

    result = await get_incident_density_handler(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        filters=make_filters(),
        db=db,
        claims={"id": str(uuid4())},
    )

    assert result.cells == []
    assert result.min_count == 0
    assert result.max_count == 0


@pytest.mark.asyncio
async def test_converts_database_errors_to_http_500():
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("database unavailable")

    with pytest.raises(HTTPException) as exc_info:
        await get_incident_density_handler(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            filters=make_filters(),
            db=db,
            claims={"id": str(uuid4())},
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to retrieve incident density"


@pytest.mark.asyncio
async def test_query_contains_date_and_viewport_filters():
    db = make_db([])

    filters = make_filters()

    await get_incident_density_handler(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        filters=filters,
        db=db,
        claims={"id": str(uuid4())},
    )

    statement = db.execute.await_args.args[0]
    statement_text = str(statement)

    assert "daily_incident_density.incident_date" in statement_text
    assert "daily_incident_density.longitude" in statement_text
    assert "daily_incident_density.latitude" in statement_text
    assert "GROUP BY" in statement_text