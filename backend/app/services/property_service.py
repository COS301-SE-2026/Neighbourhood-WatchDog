from fastapi import HTTPException
from app.core.database import DbSession
from app.schemas.property import CreatePropertyReq
from app.models.property import Property
from sqlalchemy.exc import IntegrityError

async def create_property_handler(req: CreatePropertyReq, db: DbSession) -> Property :
    newProperty = Property(
        address = req.address,
        property = req.property_type
    )

    try:
        db.add(newProperty)
        db.flush()
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(500, "Failed to add to property database")

    return newProperty
