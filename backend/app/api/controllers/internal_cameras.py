
from fastapi import APIRouter, Depends, Response, status
from typing import Annotated
from app.core.database import DbSession
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.camera import ListEnabledCameras, MediaMtxAuthRequest
from app.auth.dependencies import get_authenticated_edge_agent
from app.services.camera_service import list_enabled_cameras_for_agent_handler, authorize_mediamtx_for_agent_handler


router = APIRouter(prefix="/internal", tags=["internal"])


@router.get(
    "/cameras/enabled", 
    response_model=ListEnabledCameras,
    summary="List enabled cameras for the AI worker"
)
async def list_enabled_cameras(
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
) -> ListEnabledCameras:
    """Return enabled cameras assigned to the authenticated edge agents's property."""

    return await list_enabled_cameras_for_agent_handler(
        property_id=credential.property_id, 
        db=db
    )
    

@router.post(
    "/mediamtx/auth", 
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="Authorize a MediaMTX action"

)
async def authorize_mediamtx(request: MediaMtxAuthRequest, db: DbSession) -> Response:

    return await authorize_mediamtx_for_agent_handler(
        request=request, 
        db=db
    )