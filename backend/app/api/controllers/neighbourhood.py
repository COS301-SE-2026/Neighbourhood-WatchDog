from typing import Annotated, List

from fastapi import APIRouter, Depends
from app.schemas.neighbourhood import CreateNeighbourhoodReq, CreateNeighbourhoodRes, NeighbourhoodPropertyRes
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.auth.dependencies import require_role
from app.services.neighbourhood_service import create_neighbourhood_handler, get_neighbourhood_properties_service

router = APIRouter(prefix="/neighbourhood", tags=["neighbourhood"])

@router.post("/create-neighbourhood")
async def create_neighbourhood(req: CreateNeighbourhoodReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Create neighbourhood and return the neighbourhood that was created"""
    require_role(claims, ['RESIDENT'])

    newNeighbourhood = await create_neighbourhood_handler(name=req.name, location=req.location, property_id=req.property_id, db = db, claims = claims)

    return CreateNeighbourhoodRes(
        status=201,
        message="Neighbourhood created successfully",
        data=newNeighbourhood
    )

@router.get("/properties", response_model=List[NeighbourhoodPropertyRes], status_code=200)
async def get_neighbourhood_properties(db: DbSession, claims: Annotated[dict, Depends(get_current_user)] ):
    """Get properties of all users with neighbour details"""

    require_role("RESIDENT", "NEIGHBOURHOOD_ADMIN")
    
    properties = await get_neighbourhood_properties_service(db = db, claims = claims)

    return properties