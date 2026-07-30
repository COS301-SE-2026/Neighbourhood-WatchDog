""""
GET /api/clips/{detection_event_id}

This endpoint will return a short lived S3 url for a detection event
It does contain RBAC:
    SYSTEM_ADMIN / NEIGHBOURHOOD_ADMIN = full access
    SECURITY_OFFICER = all the cameras in their neighbourhood
    RESIDENT = only PUBLIC cameras in their neighbourhood
"""

import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import config
from app.core.database import DbSession
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent
from app.models.neighbourhood_join_request import NeighbourhoodJoinRequest


router = APIRouter(prefix="/api/clips", tags=["clips"])

#presigned url valid for 5 minutes
PRESIGN_TTL = 300
#retention deafault: 7 days (can be overriden per camera via retention_policy later)
FAULT_RETENTION_DAYS = 7

S3_BUCKET = os.getenv("S3_CLIPS_BUCKET", "")



# Current flow:
# Find detection event in the db
# Verify if the clip exists
# Check whether the clip has expired
# Check whether the user is allowed to view it (RBAC)
# Generate a temporary S3 URL
# Return URL


ADMIN_ROLES = {"SYSTEM_ADMIN", "NEIGHBOURHOOD_ADMIN", "PROPERTY_ADMIN", "RESIDENT"}

#create an aws s3 client for the applications aws region
def _s3_client():
    return boto3.client(
        "s3",
        region_name=config.aws_region,
        endpoint_url=f"https://s3.{config.aws_region}.amazonaws.com"
    )


#claim: info about the authenticated user
def _check_rbac(claims: dict, camera: Camera, db: Session) -> None:
    """Raise 403 if the caller lacks permission to view this camera's footage."""

    #this assumes that the claim came from a jwt token - need to consolidate this
    role = claims.get("role", claims.get("custom:role", ""))
    user_neighbourhood = claims.get("neighbourhood_id", claims.get("custom:neighbourhood_id"))

    #admins see everything
    if role in ADMIN_ROLES:
        return

        if str(camera.neighbourhood_id) != str(user_neighbourhood):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to view footage from this neighbourhood."
            )
    
    #security officers only see what is available in their neighbourhood
    if role == "SECURITY_OFFICER":
        return
    
    if role == "RESIDENT":

        if camera.visibility != "PUBLIC":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Residents can only view public-camera footage.",

            )
        approved = (
            db.query(NeighbourhoodJoinRequest).filter_by(
                neighbourhood_id=camera.neighbourhood_id,
                user_id=claims.get("sub"),
                status="APPROVED",
            )
            .first()
        )
        if not approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your neighbourhood membership has not been approved",

            )
        return
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="Insufficient permissions to view footage.",

    )


@router.get("/{detection_event_id}")
async def get_clip_url(
    detection_event_id: str,
    db: DbSession,
    claims: dict = Depends(get_current_user),


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
    

    #load the detection event
    #fetching the detection event and its respective camera

    event: DetectionEvent | None = db.query(DetectionEvent).filter_by(
        id=detection_event_id
    ).first()

    if not event: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection event not found"

    )

    if not event.clip_s3_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No clip is available for this event"

        )


    #checking the events retention expiry
    if event.clip_expires_at and event.clip_expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This clip has expired and is no longer available",

        )

    #rbac: laoding the camera, and applying permission rules
    camera : Camera | None = db.query(Camera).filter_by(
        id=event.camera_id
    ).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"

        )

    _check_rbac(claims, camera, db)


    #generating the pre signed url
    try:
        s3 = _s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": event.clip_s3_key},
            ExpiresIn=PRESIGN_TTL,

        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Could not generate clip URL: {exc}",

        ) from exc
    
    return {
        "url": url,
        "expires_in": PRESIGN_TTL
    }