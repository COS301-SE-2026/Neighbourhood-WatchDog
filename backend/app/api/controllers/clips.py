"""
GET /api/clips/{detection_event_id}

This endpoint will return a short lived S3 url for a detection event
It does contain RBAC:
    SYSTEM_ADMIN / NEIGHBOURHOOD_ADMIN = full access
    SECURITY_OFFICER = all the cameras in their neighbourhood
    RESIDENT = only PUBLIC cameras in their neighbourhood
"""

import os
from datetime import datetime, timezone
from botocore.config import Config as BotoConfig
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy import select
from typing import Annotated

from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.models.alert import Alert
from app.models.camera import Camera, CameraVisibilityEnum
from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/clips", tags=["clips"])

#presigned url valid for 5 minutes
PRESIGN_TTL = 300
#retention deafault: 7 days (can be overriden per camera via retention_policy later)
FAULT_RETENTION_DAYS = 7

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "")
AWS_BUCKET_REGION = "eu-north-1"


# Current flow:
# Find detection event in the db
# Verify if the clip exists
# Check whether the clip has expired
# Check whether the user is allowed to view it (RBAC)
# Generate a temporary S3 URL
# Return URL



#create an aws s3 client for the applications aws region
def _s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_BUCKET_REGION,
        endpoint_url=f"https://s3.{AWS_BUCKET_REGION}.amazonaws.com",
        config=BotoConfig(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        ),
    )


#claim: info about the authenticated user
async def _check_rbac(claims: dict, camera: Camera, property_obj: Property, db: DbSession) -> None:
    """Raise 403 unless the authenticated user may review this footage."""

    cognito_sub = claims.get("sub")
    if not cognito_sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated user identity is missing.")

    user_result = await db.execute(
        select(User).where(User.cognito_sub == cognito_sub)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No application user is associated with this identity.")

    #system administrators may review all footage.
    if user.system_role == UserRole.SYSTEM_ADMIN:
        return

    #property administrator may review footage from their own property.
    property_admin_result = await db.execute(
        select(PropertyUser).where(
            PropertyUser.user_id == user.id,
            PropertyUser.property_id == property_obj.id,
            PropertyUser.is_admin.is_(True),
        )
    )
    if property_admin_result.scalar_one_or_none() is not None:
        return

    #  all remaining access is governed by neighbourhood membership.
    if property_obj.neighbourhood_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This camera is not associated with a neighbourhood.")

    membership_result = await db.execute(
        select(NeighbourhoodUser).where(
            NeighbourhoodUser.user_id == user.id,
            NeighbourhoodUser.neighbourhood_id
            == property_obj.neighbourhood_id,
        )
    )
    membership = membership_result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not belong to this camera's neighbourhood.")

    if membership.role in {NeighbourhoodRole.NEIGHBOURHOOD_ADMIN, NeighbourhoodRole.SECURITY_OFFICER}:
        return

    if membership.role == NeighbourhoodRole.RESIDENT:
        if camera.visibility == CameraVisibilityEnum.PUBLIC:
            return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Residents can only view public-camera footage.")

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view footage.")

@router.get("/{alert_id}")
async def get_clip_url(
    alert_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
):
    """
    return a pre signed s3 url for the requested clip
    repsonses:
        200 {url: string, expires_in: 300}
        404 event not found, or no clip was saved
        410 clip has expired (it has past the retention period)
        503 s3 has not been configured
    """

    if not S3_BUCKET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Clip storage has not been onfigured on this deployment",
        )

    stmt = (
        select(Alert, Camera, Property)
        .join(Camera, Alert.camera_id == Camera.id)
        .join(Property, Camera.property_id == Property.id)
        .where(Alert.id == alert_id)
    )
    
    result = await db.execute(stmt)
    record = result.one_or_none()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert or associated camera/property was not found.")

    alert, camera, property_obj = record

    if not alert.clip_s3_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No clip is available for this alert.")

    if (alert.clip_expires_at and alert.clip_expires_at < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This clip has expired and is no longer available.")

    await _check_rbac(
        claims=claims,
        camera=camera,
        property_obj=property_obj,
        db=db,
    )

    try:
        s3 = _s3_client()

        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": alert.clip_s3_key,
            },
            ExpiresIn=PRESIGN_TTL,
        )

    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate a temporary clip URL.",
        ) from exc

    return {
        "url": url,
        "expires_in": PRESIGN_TTL,
    }