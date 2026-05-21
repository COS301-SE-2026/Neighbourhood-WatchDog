from fastapi import APIRouter, Depends, HTTPException
from app.schemas.property import CreatePropertyReq, CreatePropertyRes, PropertyRes
from app.services.property_service import create_property_handler, get_user_properties_handler
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role
from typing import List

router = APIRouter(prefix="/properties", tags=["properties"])

@router.post("/create-property")
async def create_property(req: CreatePropertyReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Create property endpoint returns the property object that was created"""

    require_role(claims, ['Resident'])
    new_property = await create_property_handler(req.address, req.property_type, claims, db)

    property_res = PropertyRes(
        property_id=new_property.id,
        neighbourhood_id=new_property.neighbourhood_id,
        address=new_property.address,
        property_type=new_property.property_type,
        created_at=new_property.created_at
    )

    return CreatePropertyRes(
        status=201,
        message="Property Created Successfully",
        data=property_res
    )


@router.get("/my-properties")
async def get_user_properties(db: DbSession, claims: dict = Depends(get_current_user)) -> List[PropertyRes]:
    """Fetch all properties for the current user"""
    require_role(claims, ['Resident'])
    properties = await get_user_properties_handler(claims, db)

    return [
        PropertyRes(
            property_id=prop.id,
            neighbourhood_id=prop.neighbourhood_id,
            address=prop.address,
            property_type=prop.property_type,
            created_at=prop.created_at
        )
        for prop in properties
    ]
