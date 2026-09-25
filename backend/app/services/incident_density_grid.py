from sqlalchemy import BigInteger, cast, func

from app.models.alert import AlertStatus
from app.models.property import Property


CELL_SIZE_METRES = 100

HISTORICAL_INCIDENT_STATUSES = (
    AlertStatus.CONFIRMED.value,
    AlertStatus.RESOLVED.value
)


def incident_grid_expressions():
    point = func.ST_SetSRID(
        func.ST_MakePoint(
            Property.longitude,
            Property.latitude
        ),
        4326
    )

    projected_point = func.ST_Transform(
        point,
        3857
    )

    snapped_cell = func.ST_SnapToGrid(
        projected_point,
        CELL_SIZE_METRES
    )

    cell_centre = func.ST_Transform(
        func.ST_Translate(
            snapped_cell,
            CELL_SIZE_METRES / 2,
            CELL_SIZE_METRES / 2
        ),
        4326
    )

    grid_x = cast(
        func.ST_X(snapped_cell),
        BigInteger
    )
    grid_y = cast(
        func.ST_Y(snapped_cell),
        BigInteger
    )

    return (
        grid_x,
        grid_y,
        func.ST_Y(cell_centre),
        func.ST_X(cell_centre)
    )
