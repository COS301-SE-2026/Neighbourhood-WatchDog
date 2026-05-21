from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.detection_event import DetectionEvent
from app.schemas.alert import AlertCreate
from fastapi import HTTPException
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import DbSession
from app.models.camera import Camera
from app.schemas.alert import AlertRes


async def create_alert(db: Session, data: AlertCreate):
    try:
        detection_event = DetectionEvent(
            camera_id=data.camera_id,
            frame_timestamp=data.timestamp,
            detection_type=data.detection_type,
            confidence_score=data.confidence,
            thumbnail_url=data.thumbnail_url,
            processed=False,
        )
        db.add(detection_event)
        db.flush()

        alert = Alert(
            camera_id=data.camera_id,
            detection_event_id=detection_event.id,
            status="OPEN",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        return alert
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")



def _build_alert_res(alert: Alert) -> AlertRes:
    event = alert.detection_event
    return AlertRes(
        id=alert.id,
        camera_id=alert.camera_id,
        detection_event_id=alert.detection_event_id,
        status=alert.status,
        resolved_by=alert.resolved_by,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
        detection_type=event.detection_type if event else None,
        confidence_score=event.confidence_score if event else None,
        thumbnail_url=event.thumbnail_url if event else None,
    )


async def acknowledge_alert_handler(alert_id, db: DbSession, claims: dict) -> AlertRes:
    if not alert_id:
        raise HTTPException(400, "Alert id is required")
    if not db:
        raise HTTPException(500, "No database session")
    if not claims:
        raise HTTPException(401, "Not authenticated")

    role = claims.get("custom:role")
    if role not in ["SECURITY_OFFICER", "NEIGHBOURHOOD_ADMIN"]:
        raise HTTPException(403, "Insufficient permissions")

    try:
        alert = db.execute(select(Alert).where(Alert.id == alert_id)).scalar_one_or_none()
        if not alert:
            raise HTTPException(404, "Alert not found")

        if alert.status != "OPEN":
            raise HTTPException(409, "Alert is already acknowledged or resolved")

        alert.status = "ACKNOWLEDGED"
        db.commit()
        db.refresh(alert)

        alert_res = _build_alert_res(alert)

        from app.api.controllers.alert import broadcast

        await broadcast(
            neighbourhood_id=str(claims.get("custom:neighbourhood_id")),
            message={"event": "alert.acknowledged", "payload": alert_res.model_dump()},
        )

        return alert_res
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to acknowledge alert")


async def list_alerts_handler(
    neighbourhood_id,
    db: DbSession,
    claims: dict,
    status_filter: str | None = None,
) -> list[AlertRes]:
    if not neighbourhood_id:
        raise HTTPException(400, "Neighbourhood id is required")
    if not db:
        raise HTTPException(500, "No database session")
    if not claims:
        raise HTTPException(401, "Not authenticated")

    caller_neighbourhood = claims.get("custom:neighbourhood_id")
    if not caller_neighbourhood or caller_neighbourhood != str(neighbourhood_id):
        raise HTTPException(403, "Not authorised for this neighbourhood")

    try:
        stmt = (
            select(Alert)
            .join(Camera, Alert.camera_id == Camera.id)
            .where(Camera.neighbourhood_id == UUID(str(neighbourhood_id)))
        )

        if status_filter:
            stmt = stmt.where(Alert.status == status_filter)

        alerts = db.execute(stmt).scalars().all()
        return [_build_alert_res(a) for a in alerts]
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to list alerts")
