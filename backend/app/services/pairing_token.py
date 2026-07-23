from app.core.database import DbSession
from app.models.property import Property
from app.models.pairing_token import PairingToken
from app.schemas.pairing_token import LinkPropertyToken, LinkPropertyTokenRes

from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.exc import IntegrityError
from uuid import UUID

import secrets
import string

async def get_pairing_token_handler(
    property_id: UUID,
    db: DbSession,
) -> LinkPropertyTokenRes:
    if not property_id:
        raise HTTPException(400, "No property provided")

    if not db:
        raise HTTPException(500, "No database provided")

    # Check property exists
    stmt = Select(Property).where(Property.id == property_id)
    user_property = db.execute(stmt)


    if not user_property:
        raise HTTPException(401, "Property does not exist")
    
    # Create the pairing token and adding it to the db
    for _ in range(10):
        token = generate_pairing_token()

        try: 
            new_token = PairingToken(token=token, property_id=property_id)
            db.add(new_token)
            db.commit()
            return LinkPropertyToken(
                token=token,
                expires_at=new_token.expires_at
            )
        except IntegrityError:
            db.rollback()
            continue #try again if there is a collision

    raise RuntimeError("Failed to generate unique pairing token after 5 attempts")



def generate_pairing_token() -> str:
    """Returns a 9 character alphanumeric code"""

    CHARS = "0123456789ABCDEFJHIJKLMNOPQRSTUVWXYZ"
    raw_num = "".join(secrets.choice(CHARS) for _ in range(9))
    return f"{raw_num[:3]}-{raw_num[3:6]}-{raw_num[6:]}"