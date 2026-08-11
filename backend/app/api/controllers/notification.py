from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from typing import Annotated

from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.notification import Notification
from app.schemas.notification import NotificationRes, ListNotificationRes

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get(
    "/{alert_id}",
    response_model=ListNotificationRes,
    summary="List all notifications for a given alert",
    responses={
        403: {"description": "Insufficient permissions to view notifications for this alert"},
        404: {"description": "Alert not found"},
    },
)
async def list_notifications_for_alert(
    alert_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
):
    role = claims.get("custom:role")
    if role not in ("NEIGHBOURHOOD_ADMIN", "SYSTEM_ADMIN", "SECURITY_OFFICER"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    camera = db.execute(select(Camera).where(Camera.id == alert.camera_id)).scalar_one_or_none()
    if not camera or str(camera.neighbourhood_id) != str(caller_neighbourhood):
        raise HTTPException(status_code=403, detail="Not authorised for this alert")
    
    notifications = db.execute(select(Notification).where(Notification.alert_id == alert_id)).scalars().all()

    return ListNotificationRes(
        status=200,
        data=[NotificationRes.model_validate(n) for n in notifications]
    )