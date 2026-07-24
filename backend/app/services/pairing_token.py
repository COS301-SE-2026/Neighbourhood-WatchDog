from app.core.database import DbSession
from app.models.property import Property
from app.models.pairing_token import PairingToken
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.schemas.pairing_token import LinkPropertyToken, LinkPropertyTokenRes, EdgeAgentsCredentialsSchema, EdgeAgentsCredentialsRes

from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from uuid import UUID

import secrets
import hashlib

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
    user_property = db.execute(stmt).scalar_one_or_none()


    if not user_property:
        raise HTTPException(404, "Property does not exist")
    
    # Create the pairing token and adding it to the db
    for _ in range(10):
        token = generate_pairing_token()

        try: 
            new_token = PairingToken(token=token, property_id=property_id)
            db.add(new_token)
            db.commit()
            link_prop_token = LinkPropertyToken(
                token=token,
                expires_at=new_token.expires_at
            )

            return LinkPropertyTokenRes(
                status=200,
                data=link_prop_token
            )
        except IntegrityError:
            db.rollback()
            continue #try again if there is a collision

    raise RuntimeError("Failed to generate unique pairing token after 10 attempts")



def generate_pairing_token() -> str:
    """Returns a 9 character alphanumeric code"""

    CHARS = "23456789ABCDEFGHJKMNPQRSTUVWXYZ" #removed 0,1,I,l from the list to avoid any ambiguiry
    raw_num = "".join(secrets.choice(CHARS) for _ in range(9))
    return f"{raw_num[:3]}-{raw_num[3:6]}-{raw_num[6:]}"


async def pair_agent_handler(
    pairing_token: str,
    db: DbSession,
) -> EdgeAgentsCredentialsRes:
    if not db:
        raise HTTPException(500, "No database provided")

    try:
        stmt = Select(PairingToken).where(PairingToken.token == pairing_token).with_for_update()
        token_record = db.execute(stmt).scalar_one_or_none()

        invalid_token = (not token_record) or (token_record.expires_at < datetime.now(timezone.utc)) or (token_record.used_at)

        if invalid_token:
            raise HTTPException(400, "Token is expired or invalid. Please request a new token and try again.")

        # find the property to get the address
        stmt = Select(Property).where(Property.id == token_record.property_id)
        property_record = db.execute(stmt).scalar_one_or_none()

        # if the property does not exist raise HTTPException
        if not property_record:
            raise HTTPException(404, "Property does not exist.")

        #also make the token record in the db say used at datetime.now
        token_record.used_at = datetime.now(timezone.utc)
        db.flush()

        #add a agent credentials table  

        api_key = gen_api_key()
        hashed_key = hash_api_key(api_key)

        new_edge_agent = EdgeAgentCredential(
            property_id=property_record.id,
            key_hash=hashed_key,
        )

        db.add(new_edge_agent)
        db.flush()
        db.commit()

        agent_creds = EdgeAgentsCredentialsSchema( #Note this is the schema
            property_id=property_record.id,
            address=property_record.address,
            api_key=api_key,
            created_at=new_edge_agent.created_at
        )

        return EdgeAgentsCredentialsRes(
            status=200,
            data=agent_creds
        )

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(500, "Failed to add to property database")

def gen_api_key() -> str:
    return f"wd_{secrets.token_urlsafe(32)}" # wd = watchdog. It will be used to easily search through logs 


def hash_api_key(plaintext_key: str) -> str:
    return hashlib.sha256(plaintext_key.encode()).hexdigest()