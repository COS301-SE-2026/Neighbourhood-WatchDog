

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from app.models.alert import Alert, AlertStatus
from app.core.database import DbSession
from app.models.property import Property
from app.schemas.alert import IncidentDensityQuery

CELL_SIZE_METRES = 100

HISTORICAL_INCIDENT_STATUSES = (
    AlertStatus.CONFIRMED.value,
    AlertStatus.RESOLVED.value
)

async def get_incident_density_handler(
    neighbourhood_id: UUID,
    filters: IncidentDensityQuery,
    db: DbSession,
    claims: dict,
):
    if not claims:
        raise HTTPException(
            status_code=401, detail="Not authenticated"
        )

    point_4326 = func.ST_SetSRID(
        func.ST_MakePoint(
            Property.longitude,
            Property.latitude
        ),
        4326
    )

    projected_point = func.ST_Transform(point_4326, 3857)

    snapped_cell = func.ST_SnapToGrid(projected_point, CELL_SIZE_METRES)

    cell_centre = func.ST_Transform(
        func.ST_Translate(
            snapped_cell,
            CELL_SIZE_METRES / 2,
            CELL_SIZE_METRES / 2
        ),
        4326
    )

    grid_x = func.ST_X(snapped_cell)
    grid_y = func.ST_Y(snapped_cell)