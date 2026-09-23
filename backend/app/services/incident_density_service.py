from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.database import DbSession
from app.models.incident_density import (
    DailyIncidentDensity,
)
from app.schemas.alert import (
    IncidentDensityCell,
    IncidentDensityData,
    IncidentDensityQuery
)
from app.services.incident_density_grid import CELL_SIZE_METRES

async def get_incident_density_handler(
    neighbourhood_id: UUID,
    filters: IncidentDensityQuery,
    db: DbSession,
    claims: dict,
) -> IncidentDensityData:
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")

    statement = (
        select(
            DailyIncidentDensity.grid_x,
            DailyIncidentDensity.grid_y,
            DailyIncidentDensity.latitude,
            DailyIncidentDensity.longitude,
            func.sum(
                DailyIncidentDensity.incident_count
            ).label("incident_count")
        )
        .where(
            DailyIncidentDensity.neighbourhood_id == neighbourhood_id,
            DailyIncidentDensity.incident_date >= filters.start_date,
            DailyIncidentDensity.incident_date <= filters.end_date,
            DailyIncidentDensity.longitude >= filters.west,
            DailyIncidentDensity.longitude <= filters.east,
            DailyIncidentDensity.latitude >= filters.south,
            DailyIncidentDensity.latitude <= filters.north
        )
        .group_by(
            DailyIncidentDensity.grid_x,
            DailyIncidentDensity.grid_y,
            DailyIncidentDensity.latitude,
            DailyIncidentDensity.longitude
        )
    )

    try:
        result = await db.execute(statement)
        rows = result.mappings().all()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve incident density"
            ),
        ) from error

    cells = [
        IncidentDensityCell(
            cell_id=(
                f"{row['grid_x']}:"
                f"{row['grid_y']}"
            ),
            grid_x=float(row["grid_x"]),
            grid_y=float(row["grid_y"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            incident_count=int(
                row["incident_count"]
            ),
        )
        for row in rows
    ]

    counts = [
        cell.incident_count
        for cell in cells
    ]

    return IncidentDensityData(
        neighbourhood_id=neighbourhood_id,
        start_date=filters.start_date,
        end_date=filters.end_date,
        cell_size_metres=CELL_SIZE_METRES,
        min_count=min(counts, default=0),
        max_count=max(counts, default=0),
        cells=cells,
    )
