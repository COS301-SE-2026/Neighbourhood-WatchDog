from fastapi import APIRouter, Depends
from app.schemas.neighbourhood import CreateNeighbourhoodReq, CreateNeighbourhoodRes
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.auth.rbac import require_role
from app.services.neighbourhood_service import create_neighbourhood_handler

router = APIRouter(prefix="/neighbourhood", tags=["neighbourhood"])

@router.post("/create-neighbourhood")
async def create_neighbourhood(req: CreateNeighbourhoodReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Create neighbourhood and return the neighbourhood that was created"""
    require_role(claims, ['Resident'])

    newNeighbourhood = await create_neighbourhood_handler(name=req.name, location=req.location, property_id=req.property_id, db = db, claims = claims)

    return CreateNeighbourhoodRes(
        status=201,
        message="Neighbourhood created successfully",
        data=newNeighbourhood
    )