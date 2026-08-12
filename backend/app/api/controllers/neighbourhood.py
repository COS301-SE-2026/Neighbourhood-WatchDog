from typing import Annotated, List

from fastapi import APIRouter, Depends
from app.schemas.neighbourhood import CreateNeighbourhoodReq, CreateNeighbourhoodRes, NeighbourhoodPropertyRes
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.auth.dependencies import require_role
from app.services.neighbourhood_service import create_neighbourhood_handler, get_neighbourhood_properties_service

router = APIRouter(prefix="/neighbourhood", tags=["neighbourhood"])

@router.post(
    "/create-neighbourhood",
    response_model=CreateNeighbourhoodRes,
    status_code=201,
    responses={
        400: {"description": "No neighbourhood name given or no neighbourhood location or no property id given to link the neighbourhood to"},
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions to access property"},
        500: {"description": "No database"},
    },
)
async def create_neighbourhood(
    req: CreateNeighbourhoodReq,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
):
    """Create neighbourhood and return the neighbourhood that was created"""
    require_role('RESIDENT', 'NEIGHBOURHOOD_ADMIN')

    new_neighbourhood = await create_neighbourhood_handler(name=req.name, location=req.location, property_id=req.property_id, db = db, claims = claims)

    return CreateNeighbourhoodRes(
        status=201,
        message="Neighbourhood created successfully",
        data=new_neighbourhood
    )

@router.get(
    "/properties", 
    response_model=List[NeighbourhoodPropertyRes], 
    status_code=200,
    responses={
        400: {"description": "No neighbourhood name given or no neighbourhood location or no property id given to link the neighbourhood to"},
        404: {"description": "User not found or no properties found for the user"},
        403: {"description": "Insufficient permissions to access property"},
    },
)
async def get_neighbourhood_properties(db: DbSession, claims: Annotated[dict, Depends(get_current_user)] ):
    """Get properties of all users with neighbour details"""

    require_role("RESIDENT", "NEIGHBOURHOOD_ADMIN")
    
    properties = await get_neighbourhood_properties_service(db = db, claims = claims)

    return properties