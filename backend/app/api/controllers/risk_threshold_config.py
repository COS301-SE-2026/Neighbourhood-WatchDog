from uuid import UUID

from fastapi import APIRouter, status

from app.auth.authorization import NeighbourhoodAdminClaims, NeighbourhoodMemberClaims
from app.core.database import DbSession
from app.schemas.risk_threshold_config import (
    NeighbourhoodRiskThresholdConfigRes,
    UpdateRiskThresholdConfigReq,
)
from app.services.risk_threshold_config_service import (
    get_neighbourhood_risk_threshold_handler,
    update_neighbourhood_risk_threshold_handler,
)

router = APIRouter(prefix="/risk-threshold", tags=["risk-threshold"])

@router.get(
    "/neighbourhood/{neighbourhood_id}",
    response_model=NeighbourhoodRiskThresholdConfigRes,
    status_code=status.HTTP_200_OK,
    summary="Get Risk Threshold for a neighbourhood",
    responses={
        403: {"description": "Not authorised for this neighbourhood"},
    },
)
async def get_neighbourhood_risk_threshold(neighbourhood_id: UUID, db: DbSession, claims: NeighbourhoodMemberClaims):
    """Get Risk Threshold for a neighbourhood"""

    neighbourhood_threshold = await get_neighbourhood_risk_threshold_handler(neighbourhood_id, db, claims)

    return NeighbourhoodRiskThresholdConfigRes(
        status=200,
        message="Neighbourhood risk threshold retrieved successfully",
        data=neighbourhood_threshold
    )

@router.patch(
    "/neighbourhood/{neighbourhood_id}",
    response_model=NeighbourhoodRiskThresholdConfigRes,
    status_code=status.HTTP_200_OK,
    summary="Update Risk Threshold for a neighbourhood",
    responses={
        403: {"description": "Not authorised for this neighbourhood"},
        422: {"description": "Invalid threshold configuration"},
    },
)
async def update_neighbourhood_risk_threshold(neighbourhood_id: UUID, req: UpdateRiskThresholdConfigReq,db: DbSession, claims: NeighbourhoodAdminClaims):
    """Update Risk Threshold for a neighbourhood"""

    neighbourhood_threshold = await update_neighbourhood_risk_threshold_handler(neighbourhood_id, req, db, claims)

    return NeighbourhoodRiskThresholdConfigRes(
        status=200,
        message="Neighbourhood risk threshold retrieved successfully",
        data=neighbourhood_threshold
    )