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

def test_complete_coverage_scores_zero():
    result = calculate_danger_scores(
        incident_cells=[
            incident_cell("100:200", 10)
        ],
        cell_coverages=[
            coverage_cell("100:200", 1.0)
        ],
        calculated_at=CALCULATED_AT,
    )[0]

    assert result.coverage_sparsity == 0.0
    assert result.danger_score == 0.0


def test_partial_coverage_reduces_danger():
    result = calculate_danger_scores(
        incident_cells=[
            incident_cell("100:200", 10)
        ],
        cell_coverages=[
            coverage_cell("100:200", 0.25)
        ],
        calculated_at=CALCULATED_AT,
    )[0]

    assert result.incident_score == 1.0
    assert result.coverage_sparsity == 0.75
    assert result.danger_score == 0.75


def test_incident_counts_are_normalised():
    results = calculate_danger_scores(
        incident_cells=[
            incident_cell(
                "100:200",
                5,
                100,
                200,
            ),
            incident_cell(
                "200:200",
                10,
                200,
                200,
            ),
        ],
        cell_coverages=[],
        calculated_at=CALCULATED_AT,
    )

    assert results[0].incident_score == 0.5
    assert results[1].incident_score == 1.0


def test_missing_coverage_means_uncovered():
    result = calculate_danger_scores(
        incident_cells=[
            incident_cell("100:200", 10)
        ],
        cell_coverages=[],
        calculated_at=CALCULATED_AT,
    )[0]

    assert result.coverage_ratio == 0.0
    assert result.coverage_sparsity == 1.0
    assert result.danger_score == 1.0


def test_scores_are_clamped():
    result = calculate_danger_scores(
        incident_cells=[
            incident_cell("100:200", 10)
        ],
        cell_coverages=[
            coverage_cell("100:200", -2.0)
        ],
        calculated_at=CALCULATED_AT,
    )[0]

    assert 0.0 <= result.incident_score <= 1.0
    assert 0.0 <= result.coverage_ratio <= 1.0
    assert 0.0 <= result.coverage_sparsity <= 1.0
    assert 0.0 <= result.danger_score <= 1.0


def test_same_input_produces_same_scores():
    incidents = [
        incident_cell("100:200", 10)
    ]
    coverage = [
        coverage_cell("100:200", 0.4)
    ]

    first = calculate_danger_scores(
        incidents,
        coverage,
        CALCULATED_AT,
    )
    second = calculate_danger_scores(
        incidents,
        coverage,
        CALCULATED_AT,
    )

    assert first == second


def test_empty_incidents_returns_empty_result():
    assert (
        calculate_danger_scores(
            [],
            [],
            CALCULATED_AT,
        )
        == []
    )
