from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends
from app.schemas.neighbourhood import (
    CreateNeighbourhoodReq,
    CreateNeighbourhoodRes,
    NeighbourhoodPropertyRes,
    NeighbourhoodMemberRes,
    UpdateMemberRoleReq,
    UpdateMemberRoleRes
)
from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.auth.dependencies import require_role
from app.services.neighbourhood_service import (
    create_neighbourhood_handler,
    get_neighbourhood_properties_service,
    get_neighbourhood_members_handler,
    update_neighbourhood_member_role_handler
)

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

@router.get(
    "/{neighbourhood_id}/members",
    response_model=List[NeighbourhoodMemberRes],
    status_code=200,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Only neighbourhood admins can view members"},
        404: {"description": "Neighbourhood not found"},
    },
)
async def get_neighbourhood_members(
    neighbourhood_id: UUID,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
):
    """Get all members and their current roles for a neighbourhood."""

    require_role("NEIGHBOURHOOD_ADMIN")

    members = await get_neighbourhood_members_handler(
        neighbourhood_id=neighbourhood_id,
        db=db,
        claims=claims,
    )

    return members



@router.patch(
    "/{neighbourhood_id}/members/{member_user_id}/role",
    response_model=UpdateMemberRoleRes,
    status_code=200,
    responses={
        400: {
            "description": "Invalid role or admin cannot remove themselves before transferring admin rights"
        },
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Only neighbourhood admins can change member roles"},
        404: {"description": "Neighbourhood member not found"},
        409: {
            "description": "The role change would leave the neighbourhood without an admin"
        },
    },
)
async def update_neighbourhood_member_role(
    neighbourhood_id: UUID,
    member_user_id: UUID,
    req: UpdateMemberRoleReq,
    db: DbSession,
    claims: Annotated[dict, Depends(get_current_user)],
):
    """Change a member's role in a neighbourhood."""

    require_role("NEIGHBOURHOOD_ADMIN")

    updated_member = await update_neighbourhood_member_role_handler(
        neighbourhood_id=neighbourhood_id,
        member_user_id=member_user_id,
        new_role=req.role,
        db=db,
        claims=claims,
    )

    return UpdateMemberRoleRes(
        status=200,
        message="Neighbourhood member role updated successfully",
        data=updated_member,
    )