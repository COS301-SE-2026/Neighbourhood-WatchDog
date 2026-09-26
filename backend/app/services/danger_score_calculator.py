from dataclasses import dataclass
from datetime import datetime

from app.services.camera_coverage_grid import (
    CellCoverage,
)


@dataclass(frozen=True)
class IncidentCell:
    cell_id: str
    grid_x: int
    grid_y: int
    latitude: float
    longitude: float
    incident_count: int


@dataclass(frozen=True)
class DangerScoreResult:
    cell_id: str
    grid_x: int
    grid_y: int
    latitude: float
    longitude: float
    incident_count: int
    incident_score: float
    coverage_ratio: float
    coverage_sparsity: float
    danger_score: float
    calculated_at: datetime


def _clamp_score(value: float) -> float:
    return max(
        0.0,
        min(1.0, value),
    )


def calculate_danger_scores(
    incident_cells: list[IncidentCell],
    cell_coverages: list[CellCoverage],
    calculated_at: datetime,
) -> list[DangerScoreResult]:
    """Combine incident density with camera-coverage sparsity."""
    if not incident_cells:
        return []

    coverage_by_cell = {
        coverage.cell_id: coverage
        for coverage in cell_coverages
    }

    maximum_incident_count = max(
        max(0, cell.incident_count)
        for cell in incident_cells
    )

    results: list[DangerScoreResult] = []

    for cell in sorted(
        incident_cells,
        key=lambda item: (
            item.grid_x,
            item.grid_y,
        ),
    ):
        incident_count = max(
            0,
            cell.incident_count,
        )

        incident_score = (
            incident_count / maximum_incident_count
            if maximum_incident_count > 0
            else 0.0
        )
        incident_score = _clamp_score(
            incident_score
        )

        coverage = coverage_by_cell.get(
            cell.cell_id
        )
        coverage_ratio = _clamp_score(
            coverage.coverage_ratio
            if coverage is not None
            else 0.0
        )

        coverage_sparsity = _clamp_score(
            1.0 - coverage_ratio
        )

        danger_score = _clamp_score(
            incident_score
            * coverage_sparsity
        )

        results.append(
            DangerScoreResult(
                cell_id=cell.cell_id,
                grid_x=cell.grid_x,
                grid_y=cell.grid_y,
                latitude=cell.latitude,
                longitude=cell.longitude,
                incident_count=incident_count,
                incident_score=incident_score,
                coverage_ratio=coverage_ratio,
                coverage_sparsity=(
                    coverage_sparsity
                ),
                danger_score=danger_score,
                calculated_at=calculated_at,
            )
        )

    return results
