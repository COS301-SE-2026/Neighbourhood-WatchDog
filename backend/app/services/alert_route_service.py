from uuid import UUID

from fastapi import HTTPException, status
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select

from app.core.database import DbSession
from app.models.neighbourhood_user import (
    NeighbourhoodRole,
    NeighbourhoodUser,
)
from app.models.property import Property
from app.models.security_officer import SecurityOfficer
from app.models.user import User
from app.schemas.alert import AlertDistanceData
from app.services.neighbourhood_service import (
    is_location_stale,
)


async def calculate_property_distance_handler(
    property_id: UUID,
    db: DbSession,
    claims: dict,
) -> AlertDistanceData:
    """Calculate the distance from an officer to an alert property."""

    user_sub = claims.get("sub") if claims else None

    if not user_sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    property_location = cast(
        func.ST_SetSRID(
            func.ST_MakePoint(
                Property.longitude,
                Property.latitude,
            ),
            4326,
        ),
        Geography(geometry_type="POINT", srid=4326,)
    )

    distance_metres = func.ST_Distance(
        SecurityOfficer.last_known_location,
        property_location,
    ).label("distance_metres")

    statement = (
        select(
            Property.id.label("property_id"),
            Property.latitude.label(
                "property_latitude"
            ),
            Property.longitude.label(
                "property_longitude"
            ),
            SecurityOfficer.last_known_location
            .is_not(None)
            .label("has_officer_location"),
            SecurityOfficer.location_updated_at.label(
                "officer_location_updated_at"
            ),
            distance_metres,
        )
        .select_from(Property)
        .join(
            NeighbourhoodUser,
            NeighbourhoodUser.neighbourhood_id == Property.neighbourhood_id,
        )
        .join(
            SecurityOfficer,
            SecurityOfficer.neighbourhood_user_id == NeighbourhoodUser.id,
        )
        .join(
            User,
            User.id == NeighbourhoodUser.user_id,
        )
        .where(
            Property.id == property_id,
            User.cognito_sub == user_sub,
            NeighbourhoodUser.role == NeighbourhoodRole.SECURITY_OFFICER,
        )
    )

    result = await db.execute(statement)
    row = result.one_or_none()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=("Property was not found in the officer's neighbourhood"))

    if (row.property_latitude is None or row.property_longitude is None):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Alert property location is unavailable")

    if not row.has_officer_location:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Officer location is unavailable")

    if is_location_stale(
        row.officer_location_updated_at,
    ):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Officer location is stale")

    if row.distance_metres is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Distance could not be calculated")

    return AlertDistanceData(
        property_id=row.property_id,
        distance_metres=float(
            row.distance_metres,
        ),
        officer_location_updated_at=(
            row.officer_location_updated_at
        ),
    )
