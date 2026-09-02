from datetime import datetime
from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user, require_role
from app.core.database import DbSession
from app.schemas.risk_score_history import NeighbourhoodRiskScoreHistoryRes, NeighbourhoodRiskScoreRes
from app.services.risk_score_history_service import get_neighbourhood_score_handler, get_neighbourhood_score_history_handler


router = APIRouter(prefix="/risk-score", tags=["risk-score"])


@router.get(
    "/neighbourhood/{neighbourhood_id}",
    response_model=NeighbourhoodRiskScoreRes,
    status_code=status.HTTP_200_OK,
    summary="Get Risk Score for a Neighbourhood",
    responses={
        403: {"description": "Not authorised for this neighbourhood"},
        404: {"description": "No risk score calculated for this neighbourhood"},
    },
)
async def get_neighbourhood_score(neighbourhood_id: UUID, db: DbSession, claims: Annotated[dict, Depends(require_role('NEIGHBOURHOOD_ADMIN', 'RESIDENT'))]):
    """Get Risk Score for a Neighbourhood"""


    neighbourhood_risk = await get_neighbourhood_score_handler(neighbourhood_id, db, claims)

    return NeighbourhoodRiskScoreRes(
        status=200,
        message="Risk Score retrieved successfully",
        data=neighbourhood_risk
    )

@router.get(
    "/neighbourhood/{neighbourhood_id}/history",
    response_model=NeighbourhoodRiskScoreHistoryRes,
    status_code=status.HTTP_200_OK,
    summary="Get Risk Score History of a Neighbourhood",
    responses={
        400: {"description": "Invalid granularity"},
        403: {"description": "Not authorised for this neighbourhood"},
        404: {"description": "Neighbourhood does not have risk score history"},
    },
)
async def get_neighbourhood_score_history(neighbourhood_id: UUID, granularity: str,db: DbSession, claims: Annotated[dict, Depends(require_role('RESIDENT','NEIGHBOURHOOD_ADMIN'))], start: datetime | None = None, end: datetime | None = None,):
    """Get Risk Score History of a Neighbourhood"""



    neighbourhood_risk_history = await get_neighbourhood_score_history_handler(neighbourhood_id, granularity, db, claims, start, end)

    return NeighbourhoodRiskScoreHistoryRes(
        status=200,
        message="Risk Score history retrieved successfully",
        data=neighbourhood_risk_history
    )