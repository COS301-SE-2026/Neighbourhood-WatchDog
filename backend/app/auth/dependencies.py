from fastapi import HTTPException, Request, Depends, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import Select
from typing import Annotated
import os
import hmac
import hashlib

from app.models.user import User
from app.core.database import get_db, DbSession
from app.auth.jwt import get_authenticated_claims
from app.models.edge_agent_credentials import EdgeAgentCredential

# default mock identity
# TODO: remove mock when Cognito is live
# change these to test different baseline states without touching headers

TESTING = os.environ.get("TESTING", "false").lower() == "true"
CUSTOM_ROLE_CLAIM = "custom:role"
CUSTOM_NEIGHBOURHOOD_CLAIM = "custom:neighbourhood_id"


def get_current_user(request: Request, db: Session = Depends(get_db)):

    claims = getattr(request.state, "claims", None)
    
    if claims is None:
        claims = get_authenticated_claims(request)
    
    sub = claims["sub"]

    if TESTING:
        return {
            "sub": request.headers.get("X-Mock-Sub", "00000000-0000-0000-0000-000000000000"),
            "given_name": "Test",
            "family_name": "User",
            CUSTOM_ROLE_CLAIM: request.headers.get("X-Mock-Role", "SYSTEM_ADMIN"),
            CUSTOM_NEIGHBOURHOOD_CLAIM: request.headers.get("X-Mock-Neighbourhood-Id"),
        }

    user = (
        db.query(User)
        .filter(User.cognito_sub == sub)
        .first()
    )

    if user is None:
        if not TESTING:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        else:
            return {
                "sub": request.headers.get("X-Mock-Sub", "00000000-0000-0000-0000-000000000000"),
                "given_name": "Test",
                "family_name": "User",
                CUSTOM_ROLE_CLAIM: request.headers.get("X-Mock-Role", "SYSTEM_ADMIN"),
                CUSTOM_NEIGHBOURHOOD_CLAIM: request.headers.get("X-Mock-Neighbourhood-Id"),
            }


    return {
        "sub": sub,
        "given_name": user.first_name,
        "family_name": user.last_name,
        CUSTOM_ROLE_CLAIM: user.role.value,
        CUSTOM_NEIGHBOURHOOD_CLAIM: (
            str(user.neighbourhood_id)
            if user.neighbourhood_id
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

def get_authenticated_edge_agent(
    db: DbSession,
    x_internal_token: Annotated[str, Header()],
) -> EdgeAgentCredential:
    provided_hash = hashlib.sha256(x_internal_token.encode()).hexdigest()

    stmt = Select(EdgeAgentCredential).where(
        EdgeAgentCredential.key_hash == provided_hash,
        EdgeAgentCredential.revoked_at.is_(None),
    )
    credential = db.execute(stmt).scalar_one_or_none()

    if credential is None:
        raise HTTPException(401, "Invalid or revoked edge agent credential.")

    return credential