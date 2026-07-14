from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role


router = APIRouter(prefix="/risk-threshold", tags=["risk-threshold"])

@router.get("/neighbourhood/{neighbourhood_id}", status_code=status.HTTP_200_OK)
def get_neighbourhood_risk_threshold(neighbourhood_id: UUID, db: DbSession, claims: Annotated[dict ,Depends(get_current_user)]):
    pass

@router.patch("/neighbourhood/{neighbourhood_id}", status_code=status.HTTP_200_OK)
def update_neighbourhood_risk_threshold(neighbourhood_id: UUID, db: DbSession, claims: Annotated[dict ,Depends(get_current_user)]):
    pass