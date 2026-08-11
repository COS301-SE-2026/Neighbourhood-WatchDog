from fastapi import HTTPException, Request, Depends, status, Header
from sqlalchemy import select
from typing import Annotated
import os
import hashlib
import logging

from app.models.user import User
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.core.database import DbSession
from app.auth.jwt import get_authenticated_claims
from app.models.edge_agent_credentials import EdgeAgentCredential

# default mock identity
# TODO: remove mock when Cognito is live
# change these to test different baseline states without touching headers

logger = logging.getLogger(__name__)

TESTING = os.environ.get("TESTING", "false").lower() == "true"
CUSTOM_ROLE_CLAIM = "custom:role"
CUSTOM_NEIGHBOURHOOD_CLAIM = "custom:neighbourhood_id"


async def get_current_user(
    request: Request, 
    db: DbSession,
) -> dict:
    """Gets the current user and returns the user's ID, cognito sub, given name, family name, custom role claim, and neighbourhood claim."""
    claims = getattr(request.state, "claims", None)
    
    if claims is None:
        claims = get_authenticated_claims(request)
    
    sub = claims["sub"]

    if TESTING:
        logger.info("get_current_user: TESTING is on. Returning mock user.")
        return {
            "id": request.headers.get("X-Mock-User-Id","00000000-0000-0000-0000-000000000000"),
            "sub": request.headers.get("X-Mock-Sub", "00000000-0000-0000-0000-000000000000"),
            "given_name": "Test",
            "family_name": "User",
            CUSTOM_ROLE_CLAIM: request.headers.get("X-Mock-Role", "SYSTEM_ADMIN"),
            CUSTOM_NEIGHBOURHOOD_CLAIM: request.headers.get("X-Mock-Neighbourhood-Id"),
        }

    stmt = select(User).where(User.cognito_sub == sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        if not TESTING:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        else:
            logger.info("get_current_user: TESTING is on. Returning mock user.")
            return {
                "id": request.headers.get("X-Mock-User-Id","00000000-0000-0000-0000-000000000000"),
                "sub": request.headers.get("X-Mock-Sub", "00000000-0000-0000-0000-000000000000"),
                "given_name": "Test",
                "family_name": "User",
                CUSTOM_ROLE_CLAIM: request.headers.get("X-Mock-Role", "SYSTEM_ADMIN"),
                CUSTOM_NEIGHBOURHOOD_CLAIM: request.headers.get("X-Mock-Neighbourhood-Id"),
            }


    stmt = (
        select(Property)
        .join(PropertyUser, PropertyUser.property_id == Property.id)
        .where(PropertyUser.user_id == user.id)
    )
    result = await db.execute(stmt)
    properties = result.scalars().all()

    neighbourhood_id = properties[0].neighbourhood_id if (properties and (len(properties) > 0)) else None
    # TODO: Fix this custom claims neighbourhood issue


    logger.info("get_current_user: returning user info.")
    return {
        "id": str(user.id),
        "sub": sub,
        "given_name": user.first_name,
        "family_name": user.last_name,
        CUSTOM_ROLE_CLAIM: user.system_role.value,
        CUSTOM_NEIGHBOURHOOD_CLAIM: (
            str(neighbourhood_id)
            if neighbourhood_id
            else None
        ),
    }

def require_role(*allowed_roles: str):#input any number of roles that are allowed and it will check for you
    """Dependency function to check if the current user has one of the allowed roles. If allowed, then will return current user"""
    def role_checker(current_user: dict = Depends(get_current_user)):

        user_role = current_user[CUSTOM_ROLE_CLAIM]

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker

# edge agents auth stuff

async def get_authenticated_edge_agent(
    db: DbSession,
    x_internal_token: Annotated[str, Header()],
) -> EdgeAgentCredential:
    """Authenticates API key (x_internal_token) and returns the credentials of the edge 
        agent associated with that API key"""
    provided_hash = hashlib.sha256(x_internal_token.encode()).hexdigest()

    stmt = select(EdgeAgentCredential).where(
        EdgeAgentCredential.key_hash == provided_hash,
        EdgeAgentCredential.revoked_at.is_(None),
    )
    result = await db.execute(stmt)
    credential = result.scalar_one_or_none()

    if credential is None:
        raise HTTPException(401, "Invalid or revoked edge agent credential.")

    return credential

async def get_user_by_claims(claims: dict, db: DbSession) -> User | None:
    """Receives the claims dictionary and DbSession and returns the User object associated with it. 
        Returns None if there is a problem. 
        Does not raise any exceptions"""

    if claims is None:
        logger.warning("get_user_by_claims: could not fetch user because claims is None")
        return None

    cognito_sub = claims['sub']

    if cognito_sub is None:
        return None

    stmt = select(User).where(User.cognito_sub == cognito_sub)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    return user