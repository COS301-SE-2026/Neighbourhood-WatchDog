from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.database import DbSession
from app.models.danger_zone import DangerZoneCell
from app.schemas.danger_zone import (
    DangerZoneCellResponse,
    DangerZoneData,
    DangerZoneQuery,
)
from app.services.camera_coverage_grid import (
    web_mercator_to_wgs84,
)
from app.services.incident_density_grid import CELL_SIZE_METRES


async def get_danger_zones_handler(
    neighbourhood_id: UUID,
    filters: DangerZoneQuery,
    db: DbSession,
    claims: dict,
) -> DangerZoneData:
    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        latest_window_end = await db.scalar(
            select(func.max(DangerZoneCell.window_end)).where(
                DangerZoneCell.neighbourhood_id
                == neighbourhood_id,
            )
        )

        if latest_window_end is None:
            return DangerZoneData(
                neighbourhood_id=neighbourhood_id,
                window_start=None,
                window_end=None,
                calculated_at=None,
                cell_size_metres=CELL_SIZE_METRES,
                min_score=0.0,
                max_score=0.0,
                cells=[],
            )

        statement = (
            select(DangerZoneCell)
            .where(
                DangerZoneCell.neighbourhood_id
                == neighbourhood_id,
                DangerZoneCell.window_end
                == latest_window_end,

                # The cached cell centre must be inside
                # the currently visible viewport.
                DangerZoneCell.longitude >= filters.west,
                DangerZoneCell.longitude <= filters.east,
                DangerZoneCell.latitude >= filters.south,
                DangerZoneCell.latitude <= filters.north,
            )
            .order_by(
                DangerZoneCell.grid_x,
                DangerZoneCell.grid_y,
            )
        )

        result = await db.execute(statement)
        rows = result.scalars().all()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve danger zones",
        ) from error

    if not rows:
        return DangerZoneData(
            neighbourhood_id=neighbourhood_id,
            window_start=None,
            window_end=latest_window_end,
            calculated_at=None,
            cell_size_metres=CELL_SIZE_METRES,
            min_score=0.0,
            max_score=0.0,
            cells=[],
        )

    cells: list[DangerZoneCellResponse] = []

    for row in rows:
        cell_size = int(
            row.cell_size_metres
            or CELL_SIZE_METRES
        )

        south, west = web_mercator_to_wgs84(
            float(row.grid_x),
            float(row.grid_y),
        )

        north, east = web_mercator_to_wgs84(
            float(row.grid_x + cell_size),
            float(row.grid_y + cell_size),
        )

        cells.append(
            DangerZoneCellResponse(
                cell_id=(
                    f"{row.grid_x}:{row.grid_y}"
                ),
                grid_x=int(row.grid_x),
                grid_y=int(row.grid_y),
                latitude=float(row.latitude),
                longitude=float(row.longitude),
                south=south,
                west=west,
                north=north,
                east=east,
                incident_count=int(
                    row.incident_count
                ),
                incident_score=float(
                    row.incident_score
                ),
                coverage_ratio=float(
                    row.coverage_ratio
                ),
                coverage_sparsity=float(
                    row.coverage_sparsity
                ),
                danger_score=float(
                    row.danger_score
                ),
            )
        )

    scores = [
        cell.danger_score
        for cell in cells
    ]

    return DangerZoneData(
        neighbourhood_id=neighbourhood_id,
        window_start=rows[0].window_start,
        window_end=rows[0].window_end,
        calculated_at=rows[0].calculated_at,
        cell_size_metres=int(
            rows[0].cell_size_metres
            or CELL_SIZE_METRES
        ),
        min_score=min(scores),
        max_score=max(scores),
        cells=cells,
    )