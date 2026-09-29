from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.auth.authorization import Claims, NeighbourhoodMemberClaims
from app.core.database import DbSession
from app.schemas.alert import (
    IncidentDetailResponse,
    ListIncidentsRes,
    Pagination,
)
from app.services.incident_service import (
    get_incident_handler,
    list_incidents_handler,
)

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)


@router.get(
    "/neighbourhoods/{neighbourhood_id}",
    response_model=ListIncidentsRes,
)
async def list_incidents(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: NeighbourhoodMemberClaims,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    camera_id: Annotated[UUID | None, Query()] = None,
    detection_type: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    results, total = await list_incidents_handler(
        neighbourhood_id=neighbourhood_id,
        db=db,
        claims=claims,
        status_filter=status_filter,
        camera_id=camera_id,
        detection_type=detection_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return ListIncidentsRes(
        status=200,
        data=results,
        pagination=Pagination(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
)
async def get_incident(
    incident_id: UUID,
    db: DbSession,
    claims: Claims,
):
    result = await get_incident_handler(
        incident_id=incident_id,
        db=db,
        claims=claims,
    )

    return IncidentDetailResponse(
        status=200,
        data=result,
    )
