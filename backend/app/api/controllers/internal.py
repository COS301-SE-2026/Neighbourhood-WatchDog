#internal endpoints for ai service communication
#uses API for auth
import base64
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth.dependencies import get_authenticated_edge_agent
from app.core.database import DbSession
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.alert import (
    AlertClipUpdateRes,
    ClipUploadAcceptedRes,
    CreateInternalAlertRequest,
    InternalAlertCreateRes,
    UpdateAlertClipRequest,
)
from app.services.alert_service import (
    create_alert_for_agent_handler,
    update_alert_clip_for_agent_handler,
    get_alert_for_agent,
)
from app.tasks.clip_tasks import MAX_CLIP_SIZE_BYTES, upload_alert_clip_task

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


@router.post(
    "/alerts/{alert_id}/clip",
    status_code=202,
    response_model=ClipUploadAcceptedRes,
    responses={
        400: {"description": "Empty or invalid clip upload"},
        401: {"description": "Invalid or revoked edge agent credential"},
        404: {"description": "Alert not found for this edge agent property"},
        413: {"description": "Clip exceeds the upload limit"},
    },
)
async def upload_clip(
    alert_id: str,
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
    clip: Annotated[UploadFile, File(...)]
) -> ClipUploadAcceptedRes:
    """Receive an H.264 MP4 from an authenticated Edge Agent and queue it for upload."""
    if clip.content_type not in {"video/mp4", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Clip upload must use video/mp4 content type")

    clip_bytes = await clip.read()

    if not clip_bytes:
        raise HTTPException(status_code=400, detail= "The uploaded clip is empty")
    if len(clip_bytes) > MAX_CLIP_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Clip exceeds the 5MB upload limit")

    alert = await get_alert_for_agent(alert_id, credential, db)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    clip_b64 = base64.b64encode(clip_bytes).decode("ascii")
    upload_alert_clip_task.delay(str(alert.id), clip_b64, clip.content_type or "video/mp4")

    return ClipUploadAcceptedRes(alert_id=alert.id, status="queued")