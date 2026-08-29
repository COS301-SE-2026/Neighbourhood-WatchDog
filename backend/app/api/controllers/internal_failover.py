from typing import Annotated
from fastapi import APIRouter, Header, status
from app.core.database import DbSession
from app.schemas.edge_failover import FailoverCameraRes
from app.services.edge_failover_service import list_failover_cameras, require_failover_controller_token


router = APIRouter(
    prefix="/internal", 
    tags=["internal failover"]
)


@router.get(
    "/failover/cameras", 
    response_model=FailoverCameraRes, 
    status_code=status.HTTP_200_OK
)
async def failover_cameras(db: DbSession, x_failover_token: Annotated[str | None, Header()] = None) -> FailoverCameraRes:

    require_failover_controller_token(x_failover_token)

    return await list_failover_cameras(db)