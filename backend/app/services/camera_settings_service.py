from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from app.core.database import DbSession
from app.models.camera import Camera
from app.models.camera_detection_zone import CameraDetectionZone

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


def update_camera_settings_handler(camera_id: UUID, confidence_threshold: float, db: DbSession) -> dict:
    camera = db.execute(
        select(Camera).where(Camera.id == camera_id)
    ).scalar_one_or_none()

    if not camera:
        raise HTTPException(404, CAMERA_NOT_FOUND)

    camera.confidence_threshold = confidence_threshold
    db.commit()
    db.refresh(camera)

    return {
        "camera_id": camera.id,
        "confidence_threshold": camera.confidence_threshold,
    }


def create_zone_handler(camera_id: UUID, name: str, polygon: list, db: DbSession) -> CameraDetectionZone:
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