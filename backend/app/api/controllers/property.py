from fastapi import APIRouter, Depends, HTTPException
from app.schemas.property import CreatePropertyReq, CreatePropertyRes, PropertyRes
from app.services.property_service import create_property_handler
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.auth.rbac import require_role

router = APIRouter(prefix="/properties", tags=["properties"])

@router.post("/create-property")
async def create_property(req: CreatePropertyReq, db: DbSession, claims: dict = Depends(get_current_user)):
    """Create property endpoint returns the property object that was created"""

    require_role(claims, ['Resident'])
    new_property, user_id = await create_property_handler(req.address, req.property_type, claims, db)

    property_res = PropertyRes(
        user_id=user_id,
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
