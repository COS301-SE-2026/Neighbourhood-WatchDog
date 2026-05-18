from fastapi import APIRouter, Depends
from app.schemas.neighbourhood import CreateNeighbourhoodReq, CreateNeighbourhoodRes
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from auth.rbac import require_role
from app.services.neighbourhood_service import create_neighbourhood_handler

router = APIRouter(prefix="/neighbourhoods", tags=["properties"])

@router.post("create-neighbourhood")
async def create_neighbourhood(req: CreateNeighbourhoodReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Create neighbourhood and return the neighbourhood that was created"""
    require_role['Resident']

    newNeighbourhood = await create_neighbourhood_handler(req.name, req.location, db, claims)

    return CreateNeighbourhoodRes(
        201,
        "Neighbourhood created successfully",
        newNeighbourhood
    )