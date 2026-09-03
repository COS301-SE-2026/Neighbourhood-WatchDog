from typing import List
from uuid import UUID

from fastapi import APIRouter

from app.auth.authorization import Claims, PropertyAdminClaims, PropertyMemberClaims
from app.core.database import DbSession
from app.schemas.property import CreatePropertyReq, CreatePropertyRes, InvitePropertyReq, InvitePropertyRes, PropertyMembers, PropertyRes
from app.services.property_service import (
    create_property_handler,
    get_property_details_handler,
    get_property_members_handler,
    get_user_properties_handler,
    invite_property_member_handler,
    remove_property_member_handler,
)

router = APIRouter(prefix="/properties", tags=["properties"])

@router.post(
    "/create-property",
    response_model=CreatePropertyRes,
    status_code=201,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions to create a property"},
    },
)
async def create_property(
    req: CreatePropertyReq,
    db: DbSession,
    claims: Claims,
):
    """Create property endpoint returns the property object that was created"""
    
    new_property = await create_property_handler(
        req.address, 
        req.property_type, 
        claims, 
        db, 
        latitude=req.latitude, 
        longitude=req.longitude
    )

    property_res = PropertyRes(
        property_id=new_property.id,
        neighbourhood_id=new_property.neighbourhood_id,
        address=new_property.address,
        property_type=new_property.property_type,
        latitude=new_property.latitude, 
        longitude=new_property.longitude, 
        created_at=new_property.created_at
    )

    return CreatePropertyRes(
        status=201,
        message="Property Created Successfully",
        data=property_res
    )


@router.get(
    "/my-properties",
    response_model=List[PropertyRes],
    status_code=200,
    responses={
        401: {"description": "Invalid or missing authentication token"},
        403: {"description": "Insufficient permissions to access property"},
    },
)
async def get_user_properties(
    db: DbSession, 
    claims: Claims,
) -> List[PropertyRes]:
    """Fetch all properties for the current user"""
    
    properties = await get_user_properties_handler(claims, db)

    return [
        PropertyRes(
            property_id=prop.id,
            neighbourhood_id=prop.neighbourhood_id,
            address=prop.address,
            property_type=prop.property_type,
            latitude=prop.latitude, 
            longitude=prop.longitude, 
            created_at=prop.created_at
        )
        for prop in properties
    ]

@router.get("/{property_id}")
async def get_property_details(
    property_id: UUID,
    db: DbSession,
    claims: PropertyMemberClaims,
):
    """Fetch property details including users, neighbourhood, and cameras"""
    return await get_property_details_handler(property_id, db, claims)

@router.get("/{property_id}/members", response_model=PropertyMembers)
async def get_property_members(
    property_id: UUID,
    db: DbSession,
    claims: PropertyMemberClaims
):
    """Fetch property members"""

    return await get_property_members_handler(property_id, db, claims)


@router.post("/{property_id}/member", response_model=InvitePropertyRes)
async def invite_property_member(
    req: InvitePropertyReq,
    property_id: UUID,
    db: DbSession,
    claims: PropertyAdminClaims
):
    """Sen an invite for user to join current property"""

    return await invite_property_member_handler(req, property_id, db, claims)

@router.delete("/{property_id}/members/{user_id}", status_code=204)
async def remove_property_member(
    property_id: UUID,
    user_id: UUID,
    db: DbSession,
    claims: PropertyAdminClaims
):
    """Remove a non-admin member from a property."""

    await remove_property_member_handler(
        property_id=property_id,
        user_id=user_id,
        db=db,
        claims=claims
    )