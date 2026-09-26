from datetime import (
    date,
    datetime,
    timedelta,
    timezone
)
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.danger_zone import DangerZoneCell
from app.models.incident_density import (
    DailyIncidentDensity,
)
from app.services.camera_coverage_calculation_service import (
    calculate_neighbourhood_cell_coverage,
)
from app.services.camera_coverage_grid import GridCell
from app.services.danger_score_calculator import (
    IncidentCell,
    calculate_danger_scores,
)
from app.services.incident_density_grid import (
    CELL_SIZE_METRES,
)


DANGER_WINDOW_DAYS = 30


async def rebuild_neighbourhood_danger_zone(
    neighbourhood_id: UUID,
    target_date: date,
    db: AsyncSession,
    calculated_at: datetime | None = None,
) -> int:
    """Rebuild one neighbourhood's danger-zone snapshot."""
    window_end = target_date
    window_start = (
        target_date
        - timedelta(
            days=DANGER_WINDOW_DAYS - 1
        )
    )

    statement = (
        select(
            DailyIncidentDensity.grid_x,
            DailyIncidentDensity.grid_y,
            DailyIncidentDensity.latitude,
            DailyIncidentDensity.longitude,
            func.sum(
                DailyIncidentDensity.incident_count
            ).label("incident_count"),
        )
        .where(
            DailyIncidentDensity.neighbourhood_id
            == neighbourhood_id,
            DailyIncidentDensity.incident_date
            >= window_start,
            DailyIncidentDensity.incident_date
            <= window_end,
        )
        .group_by(
            DailyIncidentDensity.grid_x,
            DailyIncidentDensity.grid_y,
            DailyIncidentDensity.latitude,
            DailyIncidentDensity.longitude,
        )
        .order_by(
            DailyIncidentDensity.grid_x,
            DailyIncidentDensity.grid_y,
        )
    )

    result = await db.execute(statement)
    rows = result.mappings().all()

    incident_cells = [
        IncidentCell(
            cell_id=(
                f"{row['grid_x']}:"
                f"{row['grid_y']}"
            ),
            grid_x=int(row["grid_x"]),
            grid_y=int(row["grid_y"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            incident_count=int(
                row["incident_count"]
            ),
        )
        for row in rows
    ]

    grid_cells = [
        GridCell(
            grid_x=cell.grid_x,
            grid_y=cell.grid_y,
        )
        for cell in incident_cells
    ]

    coverage_results = (
        await calculate_neighbourhood_cell_coverage(
            neighbourhood_id=neighbourhood_id,
            cells=grid_cells,
            db=db,
        )
    )

    calculation_time = (
        calculated_at
        if calculated_at is not None
        else datetime.now(timezone.utc)
    )

    danger_results = calculate_danger_scores(
        incident_cells=incident_cells,
        cell_coverages=coverage_results,
        calculated_at=calculation_time,
    )

    # Deletion and insertion remain in the same transaction.
    # A rollback therefore preserves the previous snapshot.
    await db.execute(
        delete(DangerZoneCell).where(
            DangerZoneCell.neighbourhood_id == neighbourhood_id,
            DangerZoneCell.window_end == window_end
        )
    )

    db.add_all(
        [
            DangerZoneCell(
                neighbourhood_id=neighbourhood_id,
                window_start=window_start,
                window_end=window_end,
                cell_size_metres=(
                    CELL_SIZE_METRES
                ),
                grid_x=result.grid_x,
                grid_y=result.grid_y,
                latitude=result.latitude,
                longitude=result.longitude,
                incident_count=(
                    result.incident_count
                ),
                incident_score=(
                    result.incident_score
                ),
                coverage_ratio=(
                    result.coverage_ratio
                ),
                coverage_sparsity=(
                    result.coverage_sparsity
                ),
                danger_score=(
                    result.danger_score
                ),
                calculated_at=(
                    result.calculated_at
                ),
            )
            for result in danger_results
        ]
    )

    await db.commit()

    return len(danger_results)
