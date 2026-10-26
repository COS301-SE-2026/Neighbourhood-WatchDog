from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.core.database import DbSession
from app.auth.dependencies import get_authenticated_edge_agent
from app.schemas.detection import DetectionIngestReq, DetectionIngestRes
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.services.detection_service import ingest_detection_handler

router = APIRouter(prefix="/internal", tags=["internal"])

@router.post(
    "/detections",
    response_model=DetectionIngestRes,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a detection result from the worker",
    responses={
        400: {
            "description": (
                "Invalid detection type or confidence score. "
                "Confidence score must be between 0 and 1."
            )
        },
        401: {
            "description": "Invalid internal authentication token"
        },
        500: {
            "description": "No database session or failed to ingest detection"
        },
    },
)
async def ingest_detection(
    body: DetectionIngestReq,
    db: DbSession,
    credential: Annotated[EdgeAgentCredential, Depends(get_authenticated_edge_agent)],
):
    # internal endpoint, block it at the load balancer in prod
    claims = {"sub": "system"}
    return await ingest_detection_handler(body, db, claims)
