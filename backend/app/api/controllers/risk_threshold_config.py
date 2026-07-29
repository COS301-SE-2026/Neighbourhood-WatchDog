from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role
from app.schemas.risk_threshold_config import NeighbourhoodRiskThresholdConfigRes, UpdateRiskThresholdConfigReq
from app.services.risk_threshold_config_service import get_neighbourhood_risk_threshold_handler, update_neighbourhood_risk_threshold_handler


router = APIRouter(prefix="/risk-threshold", tags=["risk-threshold"])

@router.get("/neighbourhood/{neighbourhood_id}", status_code=status.HTTP_200_OK)
def get_neighbourhood_risk_threshold(neighbourhood_id: UUID, db: DbSession, claims: Annotated[dict ,Depends(get_current_user)]):
    """Get Risk Threshold for a neighbourhood"""
    require_role(claims=claims, allowed_roles=['NEIGHBOURHOOD_ADMIN'])

    neighbourhood_threshold = get_neighbourhood_risk_threshold_handler(neighbourhood_id, db, claims)

    return NeighbourhoodRiskThresholdConfigRes(
        status=200,
        message="Neighbourhood risk threshold retrieved successfully",
        data=neighbourhood_threshold
    )

@router.patch("/neighbourhood/{neighbourhood_id}", status_code=status.HTTP_200_OK)
def update_neighbourhood_risk_threshold(neighbourhood_id: UUID, req: UpdateRiskThresholdConfigReq,db: DbSession, claims: Annotated[dict ,Depends(get_current_user)]):
    """Update Risk Threshold for a neighbourhood"""
    require_role(claims=claims, allowed_roles=['NEIGHBOURHOOD_ADMIN'])

    neighbourhood_threshold = update_neighbourhood_risk_threshold_handler(neighbourhood_id, req, db, claims)

    return NeighbourhoodRiskThresholdConfigRes(
        status=200,
        message="Neighbourhood risk threshold retrieved successfully",
        data=neighbourhood_threshold
    )