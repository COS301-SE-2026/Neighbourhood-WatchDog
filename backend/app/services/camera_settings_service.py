from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from app.models.camera import Camera
from app.models.camera_detection_zone import CameraDetectionZone

import logging

from app.services.audit_service import create_audit_log_item
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditAction, TargetEntity

CAMERA_NOT_FOUND = "Camera not found"

logger = logging.getLogger(__name__)

async def get_camera_settings_handler(camera_id: UUID, db: AsyncSession) -> dict:
    """Gets and returns the settings of the camera with the camera_id passed into the function. Returns the camera_id, confidence_threshold, and a list of camera zones in a dictionary"""
    camera_result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = camera_result.scalar_one_or_none()

    if not camera:
        logger.warning("get_camera_settings: camera with id=%s not found", camera_id)
        raise HTTPException(404, CAMERA_NOT_FOUND)

    zones_result = await db.execute(
        select(CameraDetectionZone)
        .where(CameraDetectionZone.camera_id == camera_id)
    )
    zones = zones_result.scalar_one_or_none().all()

    logger.info("get_camera_settings: successfully retrieved the settings of the camera with id=%s", camera_id)
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


async def update_camera_settings_handler(camera_id: UUID, confidence_threshold: float, db: AsyncSession, claims: dict) -> dict:
    """Updates the camera settings of the camera with the id passed in. Receives the camera_id, confidence_threshold, db, and claims. It returns a dictionary with the camera id and the new confidence threshold. """
    try:
        camera_result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = camera_result.scalar_one_or_none()

        if not camera:
            logger.warning("update_camera_settings: camera with id=%s not found", camera_id)
            raise HTTPException(404, CAMERA_NOT_FOUND)

        old_values = {
            "confidence_threshold": camera.confidence_threshold
        }

        camera.confidence_threshold = confidence_threshold

        new_values = {
            "confidence_threshold": confidence_threshold
        }

        create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.UPDATE,
            target_entity_type="Camera",
            target_entity_id=camera.id,
            old_values=old_values,
            new_values=new_values,
        )

        await db.commit()
        await db.refresh(camera)

        logger.info("update_camera_settings: successfully updated settings of camera with id=%s", camera_id)
        return {
            "camera_id": camera.id,
            "confidence_threshold": camera.confidence_threshold,
        }

    except HTTPException as he:
        await db.rollback()
        raise he

    except Exception:
        await db.rollback()
        logging.exception("Failed to update camera settings for camera_id=%s", camera_id)
        raise HTTPException(
            500,
            "Failed to update camera settings"
        )


async def create_zone_handler(camera_id: UUID, name: str, polygon: list, db: AsyncSession, claims: dict) -> CameraDetectionZone:
    """Creates a zone on the frame so that only detections found within that zone are picked up. Receives the camera_id, name, polygon, db and claims and returns the created zone."""
    try:
        camera_result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = camera_result.scalar_one_or_none()

        if not camera:
            logger.warning("create_zone: camera with id=%s not found", camera_id)
            raise HTTPException(404, CAMERA_NOT_FOUND)

        if len(polygon) < 3:
            logger.warning("create_zone: could not create zone for camera with id=%s because polygon had less than 3 sides", camera_id)
            raise HTTPException(
                400,
                "A zone polygon must have at least 3 points"
            )

        zone = CameraDetectionZone(
            camera_id=camera_id,
            name=name,
            polygon=polygon,
        )

        await db.add(zone)

        # Generates zone.id without committing
        await db.flush()

        create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.CREATE,
            target_entity_type="CameraDetectionZone",
            target_entity_id=zone.id,
            new_values={
                "camera_id": str(zone.camera_id),
                "name": zone.name,
                "polygon": zone.polygon,
            },
        )

        await db.commit()
        await db.refresh(zone)

        return zone

    except HTTPException as he:
        await db.rollback()
        raise he

    except Exception:
        await db.rollback()
        raise HTTPException(
            500,
            "Failed to create detection zone"
        )


async def delete_zone_handler(camera_id: UUID,zone_id: UUID,db: AsyncSession,claims: dict) -> None:
    try:
        zone_result = await db.execute(
            select(CameraDetectionZone).where(
                CameraDetectionZone.id == zone_id,
                CameraDetectionZone.camera_id == camera_id,
            )
        )
        zone = zone_result.scalar_one_or_none()

        if not zone:
            raise HTTPException(
                404,
                "Zone not found"
            )

        old_values = {
            "camera_id": str(zone.camera_id),
            "name": zone.name,
            "polygon": zone.polygon,
        }

        zone_id = zone.id

        await db.delete(zone)

        create_audit_log_item(
            db=db,
            user_id=UUID(claims["id"]),
            action=AuditAction.DELETE,
            target_entity_type="CameraDetectionZone",
            target_entity_id=zone_id,
            old_values=old_values,
        )

        await db.commit()

    except HTTPException as he:
        await db.rollback()
        raise he

    except Exception:
        await db.rollback()
        raise HTTPException(
            500,
            "Failed to delete detection zone"
        )