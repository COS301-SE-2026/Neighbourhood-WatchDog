
from fastapi import APIRouter, Depends, Response, status
from typing import Annotated
from app.core.cache import cache_get_or_set
from app.core.database import DbSession
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.camera import ListEnabledCameras, MediaMtxAuthRequest
from app.auth.dependencies import get_authenticated_edge_agent
from app.services.camera_service import list_enabled_cameras_for_agent_handler, authorize_mediamtx_for_agent_handler, list_camera_summaries_for_agent_handler
from app.services.camera_cache import camera_internal_cache_key
from app.services.edge_agent_heartbeat import record_edge_agent_heartbeat


router = APIRouter(prefix="/internal", tags=["internal"])

CAMERAS_ENABLED_TTL = 5 # TTL of the enabled cameras endpoint cache items

@router.get(
    "/cameras/summary",
    response_model=AgentCameraSummaryList,
    status_code=status.HTTP_200_OK,
    summary="List safe camera summaries for the desktop agent",
    responses={
        401: {
            "description": (
                "Invalid or missing edge-agent credentials"
            )
        },
    },
)
async def list_camera_summaries(db: DbSession,
    credential: Annotated[
        EdgeAgentCredential,
        Depends(get_authenticated_edge_agent),
    ],
) -> AgentCameraSummaryList:
    return await list_camera_summaries_for_agent_handler(property_id=credential.property_id, db=db)

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

    async def fetch():
        cameras = await list_enabled_cameras_for_agent_handler(
            property_id=property_id,
            db=db
        )
        return (cameras.model_dump(mode="json"))

    return await cache_get_or_set(camera_internal_cache_key(credential.property_id), CAMERAS_ENABLED_TTL, fetch)

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