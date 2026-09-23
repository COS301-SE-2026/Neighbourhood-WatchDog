

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from app.models.alert import Alert, AlertStatus
from app.core.database import DbSession
from app.models.camera import Camera
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

    statement = (
        select(
            grid_x.label("grid_x"),
            grid_y.label("grid_y"),
            func.ST_Y(cell_centre).label(
                "latitude"
            ),
            func.ST_X(cell_centre).label(
                "longitude"
            ),
            func.count(Alert.id).label(
                "incident_count"
            )
        )
        .select_from(Alert)
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .where(
            Property.neighbourhood_id == neighbourhood_id,
            Property.latitude.is_not(None),
            Property.longitude.is_not(None),
            Property.longitude >= filters.west,
            Property.longitude <= filters.east,
            Property.latitude >= filters.south,
            Property.latitude <= filters.north,
            Alert.status.in_(HISTORICAL_INCIDENT_STATUSES),
            Alert.frame_timestamp >= filters.start_at,
            Alert.frame_timestamp < filters.end_at
        )
        .group_by(
            grid_x,
            grid_y,
            cell_centre
        )
    )

    try:
        result = await db.execute(statement)
        rows = result.mappings().all()
    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to calculate incident density") from error

    
