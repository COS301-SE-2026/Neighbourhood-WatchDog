from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.danger_zone import DangerZoneCell
from app.services.camera_coverage_grid import (
    CellCoverage,
)
from app.services.danger_zone_service import (
    rebuild_neighbourhood_danger_zone,
)


@pytest.mark.asyncio
async def test_rebuild_persists_calculated_cells():
    neighbourhood_id = uuid4()
    calculated_at = datetime(
        2026,
        9,
        25,
        10,
        0,
        tzinfo=timezone.utc,
    )

    query_result = MagicMock()
    query_result.mappings.return_value.all.return_value = [
        {
            "grid_x": 100,
            "grid_y": 200,
            "latitude": -25.75,
            "longitude": 28.23,
            "incident_count": 10,
        }
    ]

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            query_result,
            MagicMock(),
        ]
    )
    db.add_all = MagicMock()
    db.commit = AsyncMock()

    coverage = [
        CellCoverage(
            cell_id="100:200",
            grid_x=100,
            grid_y=200,
            latitude=-25.75,
            longitude=28.23,
            coverage_ratio=0.25,
        )
    ]

    with patch(
        "app.services.danger_zone_service."
        "calculate_neighbourhood_cell_coverage",
        new=AsyncMock(return_value=coverage),
    ):
        count = (
            await rebuild_neighbourhood_danger_zone(
                neighbourhood_id=(
                    neighbourhood_id
                ),
                target_date=date(
                    2026,
                    9,
                    25,
                ),
                db=db,
                calculated_at=calculated_at,
            )
        )

    assert count == 1
    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()

    saved_cells = db.add_all.call_args.args[0]

    assert len(saved_cells) == 1
    assert isinstance(
        saved_cells[0],
        DangerZoneCell,
    )

    saved = saved_cells[0]

    assert saved.neighbourhood_id == neighbourhood_id
    assert saved.window_start == date(
        2026,
        8,
        27,
    )
    assert saved.window_end == date(
        2026,
        9,
        25,
    )
    assert saved.incident_count == 10
    assert saved.incident_score == 1.0
    assert saved.coverage_ratio == 0.25
    assert saved.coverage_sparsity == 0.75
    assert saved.danger_score == 0.75
    assert saved.calculated_at == calculated_at
