from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role
from app.schemas.risk_score_history import NeighbourhoodRiskScoreHistoryRes, NeighbourhoodRiskScoreRes
from app.services.risk_score_history_service import get_neighbourhood_score_handler, get_neighbourhood_score_history_handler


router = APIRouter(prefix="/risk-score", tags=["risk-score"])


@router.get("/neighbourhood/{neighbourhood_id}", status_code=status.HTTP_200_OK)
def get_neighbourhood_score(neighbourhood_id: UUID, db: DbSession, claims: Annotated[dict, Depends(get_current_user)]):
    """Get Risk Score for a Neighbourhood"""

    require_role(claims=claims, allowed_roles=['NEIGHBOURHOOD_ADMIN'])

    neighbourhood_risk = get_neighbourhood_score_handler(neighbourhood_id, db, claims)

    return NeighbourhoodRiskScoreRes(
        status=200,
        message="Risk Score retrieved successfully",
        data=neighbourhood_risk
    )

@router.get("/neighbourhood/{neighbourhood_id}/history", status_code=status.HTTP_200_OK)
def get_neighbourhood_score_history(neighbourhood_id: UUID, db: DbSession, claims: Annotated[dict, Depends(get_current_user)]):
    """Get Risk Score History of a Neighbourhood"""

    require_role(claims=claims, allowed_roles=['NEIGHBOURHOOD_ADMIN'])


    neighbourhood_risk_history = get_neighbourhood_score_history_handler(neighbourhood_id, db, claims)

    return NeighbourhoodRiskScoreHistoryRes(
        status=200,
        message="Risk Score history retrieved successfully",
        data=neighbourhood_risk_history
    )