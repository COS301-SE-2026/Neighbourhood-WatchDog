from datetime import datetime, timezone

from app.services.camera_coverage_grid import (
    CellCoverage,
)
from app.services.danger_score_calculator import (
    IncidentCell,
    calculate_danger_scores,
)


CALCULATED_AT = datetime(
    2026,
    9,
    25,
    10,
    0,
    tzinfo=timezone.utc,
)


def incident_cell(
    cell_id: str,
    incident_count: int,
    grid_x: int = 100,
    grid_y: int = 200,
) -> IncidentCell:
    return IncidentCell(
        cell_id=cell_id,
        grid_x=grid_x,
        grid_y=grid_y,
        latitude=-25.75,
        longitude=28.23,
        incident_count=incident_count,
    )


def coverage_cell(
    cell_id: str,
    coverage_ratio: float,
    grid_x: int = 100,
    grid_y: int = 200,
) -> CellCoverage:
    return CellCoverage(
        cell_id=cell_id,
        grid_x=grid_x,
        grid_y=grid_y,
        latitude=-25.75,
        longitude=28.23,
        coverage_ratio=coverage_ratio,
    )


def test_high_incidents_without_coverage_scores_one():
    results = calculate_danger_scores(
        incident_cells=[
            incident_cell("100:200", 10)
        ],
        cell_coverages=[
            coverage_cell("100:200", 0.0)
        ],
        calculated_at=CALCULATED_AT,
    )

    result = results[0]

    assert result.incident_score == 1.0
    assert result.coverage_sparsity == 1.0
    assert result.danger_score == 1.0
