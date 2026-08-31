
from fastapi import APIRouter, Depends, Response, status
from typing import Annotated
from app.core.database import DbSession
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.camera import ListEnabledCameras, MediaMtxAuthRequest
from app.auth.dependencies import get_authenticated_edge_agent
from app.services.camera_service import list_enabled_cameras_for_agent_handler, authorize_mediamtx_for_agent_handler
from app.services.edge_agent_heartbeat import record_edge_agent_heartbeat


router = APIRouter(prefix="/internal", tags=["internal"])


@router.get(
    "/cameras/enabled",
    response_model=ListEnabledCameras,
    status_code=status.HTTP_200_OK,
    summary="List enabled cameras for the AI worker",
    responses={
        401: {"description": "Invalid or missing edge agent credentials"},
        500: {"description": "Failed to retrieve enabled cameras"},
    },
)
async def list_enabled_cameras(db: DbSession, credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)]) -> ListEnabledCameras:
    """Return enabled cameras for the authenticated Edge Agent."""

    property_id = credential.property_id

    await record_edge_agent_heartbeat(
        credential=credential,
        db=db
    )

    return await list_enabled_cameras_for_agent_handler(
        property_id=property_id,
        db=db
    )

@router.post(
    "/mediamtx/auth",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Authorize a MediaMTX action",
    responses={
        204: {"description": "MediaMTX action authorized"},
        401: {"description": "Invalid camera path, credentials or disabled camera"},
        403: {"description": "MediaMTX action not allowed"},
    },
)
async def authorize_mediamtx(request: MediaMtxAuthRequest, db: DbSession) -> Response:

    return await authorize_mediamtx_for_agent_handler(
        request=request, 
        db=db
    )