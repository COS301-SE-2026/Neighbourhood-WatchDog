import os

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.database import DbSession
from app.schemas.detection import DetectionIngestReq, DetectionIngestRes
from app.services.detection_service import ingest_detection_handler

router = APIRouter(prefix="/internal", tags=["internal"])

INTERNAL_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-token")


def verify_internal_token(x_internal_token: str = Header(...)) -> None:
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


@router.post(
    "/detections",
    response_model=DetectionIngestRes,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a detection result from the worker",
    dependencies=[Depends(verify_internal_token)],
)
async def ingest_detection(
    body: DetectionIngestReq,
    db: DbSession,
):
    # internal endpoint, block it at the load balancer in prod
    claims = {"sub": "system"}
    return await ingest_detection_handler(body, db, claims)
