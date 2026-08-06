from app.core.database import DbSession
from app.models.property import Property
from app.models.camera import Camera
from app.schemas.camera import CameraRes
from app.models.pairing_token import PairingToken
from app.models.edge_agent_credentials import EdgeAgentCredential
from app.models.user import User
from app.schemas.pairing_token import LinkPropertyToken, LinkPropertyTokenRes, EdgeAgentsCredentialsSchema, EdgeAgentsCredentialsRes

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from uuid import UUID

from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction

import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

async def get_pairing_token_handler(
    property_id: UUID,
    db: DbSession,
    claims: dict
) -> LinkPropertyTokenRes:
    """Gets a pairing token. Requires the user's property_id, the dbSession, 
        and the claims. Creates the pairing token and returns it to the user 
        for the user to pair their edge agent to the property."""

    if not property_id:
        logger.warning("get_pairing_token: no property_id provided in request with claims=%s", claims)
        raise HTTPException(400, "No property ID provided")

    if not db:
        logger.warning("get_pairing_token: no db provided in request with claims=%s", claims)
        raise HTTPException(500, "No database provided")

    # Check property exists
    stmt = select(Property).where(Property.id == property_id)
    result = await db.execute(stmt)
    user_property = result.scalar_one_or_none()


    if not user_property:
        logger.warning("get_pairing_token: no property found with property_id=%s", property_id)
        raise HTTPException(404, "Property does not exist")
    
    # Create the pairing token and adding it to the db
    for _ in range(10):
        token = generate_pairing_token()

        try: 
            new_token = PairingToken(token=token, property_id=property_id)
            db.add(new_token)
            await db.flush()

            stmt = select(User).where(User.cognito_sub == claims['sub'])
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                logger.warning("get_pairing_token: user not found with cognito sub=%s", claims['sub'])
                raise HTTPException(404, "User not found.")

            await create_audit_log_item(
                db=db,
                user_id=user.id,
                action=AuditAction.CREATE,
                target_entity_type="PairingToken",
                target_entity_id=new_token.id,
                new_values={
                    "property_id": str(property_id),
                    "expires_at": new_token.expires_at.isoformat(),
                },
            )

            await db.commit()
            
            link_prop_token = LinkPropertyToken(
                token=token,
                expires_at=new_token.expires_at
            )

            return LinkPropertyTokenRes(
                status=200,
                data=link_prop_token
            )
        except IntegrityError:
            logger.error("get_pairing_token: token collision, retrying, property_id=%s", property_id)
            await db.rollback()
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
    """Receives the pairing token from the edge agent and links the property to the agent 
        by creating a record in the edge agent credentials table and return those credentials"""
    if not db:
        logger.warning("pair_agent: no db passed in for request with pairing_token=%s", pairing_token)
        raise HTTPException(500, "No database provided")

    try:
        stmt = select(PairingToken).where(PairingToken.token == pairing_token).with_for_update()
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()

        invalid_token = (not token_record) or (token_record.expires_at < datetime.now(timezone.utc)) or (token_record.used_at)

        if invalid_token:
            logger.warning("pair_agent: pairing_token %s is invalid", pairing_token)
            raise HTTPException(400, "Token is expired or invalid. Please request a new token and try again.")

        # find the property to get the address
        stmt = select(Property).where(Property.id == token_record.property_id)
        result = await db.execute(stmt)
        property_record = result.scalar_one_or_none()

        # if the property does not exist raise HTTPException
        if not property_record:
            raise HTTPException(404, "Property does not exist.")

        #also make the token record in the db say used at datetime.now
        token_record.used_at = datetime.now(timezone.utc)
        await db.flush()

        #add a agent credentials table  

        api_key = gen_api_key()
        hashed_key = hash_api_key(api_key)

        new_edge_agent = EdgeAgentCredential(
            property_id=property_record.id,
            key_hash=hashed_key,
        )

        db.add(new_edge_agent)
        await db.flush()
        await db.commit()

        #getting the cameras related to the property
        stmt = select(Camera).where(Camera.property_id == property_record.id)
        result = await db.execute(stmt)
        cameras = result.scalars().all()

        cameras_data = [
            CameraRes(
                id=c.id,
                name=c.name,
                property_id=c.property_id,
                neighbourhood_id=c.neighbourhood_id,
                rtsp_url=c.rtsp_url,
                visibility=c.visibility,
                location=c.location,
                enabled=c.enabled,
                created_at=c.created_at,
            )
            for c in cameras
        ]

        agent_creds = EdgeAgentsCredentialsSchema( #Note this is the schema
            property_id=property_record.id,
            address=property_record.address,
            api_key=api_key,
            cameras=cameras_data,
            created_at=new_edge_agent.created_at
        )

        return EdgeAgentsCredentialsRes(
            status=201,
            data=agent_creds
        )

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Failed to add to property database")

def gen_api_key() -> str:
    return f"wd_{secrets.token_urlsafe(32)}" # wd = watchdog. It will be used to easily search through logs 


def hash_api_key(plaintext_key: str) -> str:
    return hashlib.sha256(plaintext_key.encode()).hexdigest()