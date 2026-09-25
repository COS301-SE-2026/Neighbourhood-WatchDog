from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.camera_coverage import (
    MAX_CAMERA_ORIGIN_DISTANCE_METRES,
    coverage_polygon,
    haversine_distance_metres,
)
from app.models.audit_log import AuditAction, TargetEntity
from app.models.camera import Camera
from app.models.camera_coverage import CameraCoverage
from app.models.property import Property
from app.schemas.camera_coverage import CameraCoverageInput, CameraCoverageResponse
from app.services.audit_service import create_audit_log_item


CAMERA_NOT_FOUND = "Camera not found"


def _validate_origin_near_property(
    coverage: CameraCoverageInput,
    property_obj: Property,
) -> None:
    if property_obj.latitude is None or property_obj.longitude is None:
        raise HTTPException(
            status_code=400,
            detail="The property must have valid coordinates before a camera POV can be configured",
        )

    distance = haversine_distance_metres(
        property_obj.latitude,
        property_obj.longitude,
        coverage.origin_latitude,
        coverage.origin_longitude,
    )

    if distance > MAX_CAMERA_ORIGIN_DISTANCE_METRES:
        raise HTTPException(
            status_code=400,
            detail=(
                "The camera location must be within "
                f"{MAX_CAMERA_ORIGIN_DISTANCE_METRES:.0f} metres of the property"
            ),
        )


def _to_response(coverage: CameraCoverage) -> CameraCoverageResponse:
    return CameraCoverageResponse(
        id=coverage.id,
        camera_id=coverage.camera_id,
        origin_latitude=coverage.origin_latitude,
        origin_longitude=coverage.origin_longitude,
        coverage_bearing_degrees=coverage.coverage_bearing_degrees,
        coverage_angle_degrees=coverage.coverage_angle_degrees,
        coverage_range_metres=coverage.coverage_range_metres,
        polygon=coverage_polygon(
            coverage.origin_latitude,
            coverage.origin_longitude,
            coverage.coverage_bearing_degrees,
            coverage.coverage_angle_degrees,
            coverage.coverage_range_metres,
        ),
    )


async def get_camera_coverage_handler(
    camera_id: UUID,
    db: AsyncSession,
    claims: dict,
) -> CameraCoverageResponse | None:
    camera = await db.scalar(select(Camera).where(Camera.id == camera_id))

    if camera is None:
        raise HTTPException(status_code=404, detail=CAMERA_NOT_FOUND)

    coverage = await db.scalar(
        select(CameraCoverage).where(CameraCoverage.camera_id == camera_id)
    )

    if coverage is None:
        return None

    return _to_response(coverage)


async def upsert_camera_coverage_handler(
    camera_id: UUID,
    payload: CameraCoverageInput,
    db: AsyncSession,
    claims: dict,
) -> CameraCoverageResponse:
    camera_result = await db.execute(
        select(Camera, Property)
        .join(Property, Property.id == Camera.property_id)
        .where(Camera.id == camera_id)
    )
    camera_row = camera_result.one_or_none()

    if camera_row is None:
        raise HTTPException(status_code=404, detail=CAMERA_NOT_FOUND)

    camera, property_obj = camera_row
    _validate_origin_near_property(payload, property_obj)

    coverage = await db.scalar(
        select(CameraCoverage).where(CameraCoverage.camera_id == camera_id)
    )

    old_values = None

    if coverage is None:
        coverage = CameraCoverage(camera_id=camera_id)
        db.add(coverage)
    else:
        old_values = {
            "origin_latitude": coverage.origin_latitude,
            "origin_longitude": coverage.origin_longitude,
            "coverage_bearing_degrees": coverage.coverage_bearing_degrees,
            "coverage_angle_degrees": coverage.coverage_angle_degrees,
            "coverage_range_metres": coverage.coverage_range_metres,
        }

    for field, value in payload.model_dump().items():
        setattr(coverage, field, value)

    await db.flush()

    await create_audit_log_item(
        db=db,
        user_id=UUID(claims["id"]),
        action=AuditAction.UPDATE if old_values is not None else AuditAction.CREATE,
        target_entity_type=TargetEntity.CAMERA,
        target_entity_id=camera_id,
        old_values=old_values,
        new_values=payload.model_dump(mode="json"),
    )

    await db.commit()
    await db.refresh(coverage)

    return _to_response(coverage)


async def delete_camera_coverage_handler(
    camera_id: UUID,
    db: AsyncSession,
    claims: dict,
) -> None:
    camera = await db.scalar(select(Camera).where(Camera.id == camera_id))

    if camera is None:
        raise HTTPException(status_code=404, detail=CAMERA_NOT_FOUND)

    coverage = await db.scalar(
        select(CameraCoverage).where(CameraCoverage.camera_id == camera_id)
    )

    if coverage is None:
        return

    await db.delete(coverage)
    await db.commit()