from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import DbSession
from app.models.camera import Camera
from app.models.camera_detection_zone import CameraDetectionZone

from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction

CAMERA_NOT_FOUND = "Camera not found"


def get_camera_settings_handler(camera_id: UUID, db: DbSession) -> dict:
    camera = db.execute(
        select(Camera).where(Camera.id == camera_id)
    ).scalar_one_or_none()

    if not camera:
        raise HTTPException(404, CAMERA_NOT_FOUND)

    zones = db.execute(
        select(CameraDetectionZone).where(CameraDetectionZone.camera_id == camera_id)
    ).scalars().all()

    return {
        "camera_id": camera_id,
        "confidence_threshold": camera.confidence_threshold,
        "zones": [
            {
                "id": z.id,
                "camera_id": z.camera_id,
                "name": z.name,
                "polygon": z.polygon,
            }
            for z in zones
        ],
    }


def update_camera_settings_handler(camera_id: UUID, confidence_threshold: float, db: DbSession, claims: dict) -> dict:
    camera = db.execute(
        select(Camera).where(Camera.id == camera_id)
    ).scalar_one_or_none()

    if not camera:
        raise HTTPException(404, CAMERA_NOT_FOUND)

    old_values = {
        "confidence_threshold": camera.confidence_threshold
    }
    camera.confidence_threshold = confidence_threshold
    
    db.commit()
    db.refresh(camera)

    new_values = {
        "confidence_threshold": camera.confidence_threshold
    }

    create_audit_log_item(
        db=db,
        user_id=UUID(claims["id"]),
        action=AuditAction.UPDATE,
        target_entity_type="CameraSettings",
        target_entity_id=camera.id,
        old_values=old_values,
        new_values=new_values,
    )

    return {
        "camera_id": camera.id,
        "confidence_threshold": camera.confidence_threshold,
    }


def create_zone_handler(camera_id: UUID, name: str, polygon: list, db: DbSession, claims: dict) -> CameraDetectionZone:
    camera = db.execute(
        select(Camera).where(Camera.id == camera_id)
    ).scalar_one_or_none()

    if not camera:
        raise HTTPException(404, CAMERA_NOT_FOUND)

    if len(polygon) < 3:
        raise HTTPException(400, "A zone polygon must have at least 3 points")

    zone = CameraDetectionZone(camera_id=camera_id, name=name, polygon=polygon)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    
    create_audit_log_item(
        db=db,
        user_id=UUID(claims["id"]),
        action=AuditAction.CREATE,
        target_entity_type="DetectionZone",
        target_entity_id=zone.id,
        new_values={
            "camera_id": str(zone.camera_id),
            "name": zone.name,
            "polygon": zone.polygon,
        },
    )
    return zone


def delete_zone_handler(camera_id: UUID, zone_id: UUID, db: DbSession) -> None:
    zone = db.execute(
        select(CameraDetectionZone).where(
            CameraDetectionZone.id == zone_id,
            CameraDetectionZone.camera_id == camera_id,
        )
    ).scalar_one_or_none()

    if not zone:
        raise HTTPException(404, "Zone not found")

    db.delete(zone)
    db.commit()