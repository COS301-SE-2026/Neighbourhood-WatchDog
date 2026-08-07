#internal endpoints for ai service communication
#uses API for auth
from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_authenticated_edge_agent
from app.core.database import DbSession
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.alert import (
    AlertClipUpdateRes,
    CreateInternalAlertRequest,
    InternalAlertCreateRes,
    UpdateAlertClipRequest,
)
from app.services.alert_service import (
    create_alert_for_agent_handler,
    update_alert_clip_for_agent_handler,
)

router = APIRouter(prefix="/internal", tags=["internal"])



@router.post("/alerts",
    status_code=201,
    response_model=InternalAlertCreateRes,
    responses={
        404: {"description": "Camera not found"}, 
        400: {"description": "camera_id is not a valid UUID, or frame_timestamp is not a valid IOS datetime"},
        401: {"description": "Invalid or revoked edge agent credential"},
    },
)

async def create_alert(
    body: CreateInternalAlertRequest,
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
      # this line ^ is in charge of checking whether there is a valid api key associated with this or not
) -> InternalAlertCreateRes:
    """Create an alert from an authenticated AI edge-agent detection."""

    return await create_alert_for_agent_handler(
        body=body, 
        credential=credential, 
        db=db
    )
    
    

@router.patch("/alerts/{alert_id}/clip", 
    response_model=AlertClipUpdateRes,
    responses={
        404: {"description": "Alert not found"}, 
        400: {"description": "alert_id is not a valid UUID, or clip_expires_at is not a valid IOS datetime"},
        401: {"description": "Invalid or revoked edge agent credential"},
    }
)
async def update_clip(
    alert_id: str, 
    body: UpdateAlertClipRequest, 
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
) -> AlertClipUpdateRes:
    """updating s3 clip key and expiry on a detection event after ai uploads the clip"""

    return await update_alert_clip_for_agent_handler(
        alert_id=alert_id, 
        body=body, 
        credential=credential, 
        db=db
    )
    