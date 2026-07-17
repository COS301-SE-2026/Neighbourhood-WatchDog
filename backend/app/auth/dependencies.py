import os
from fastapi import HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.core.database import get_db
from app.auth.jwt import get_authenticated_claims

# default mock identity
# TODO: remove mock when Cognito is live
# change these to test different baseline states without touching headers

TESTING = os.environ.get("TESTING", "false").lower() == "true"

def get_current_user(request: Request, db: Session = Depends(get_db)):

    claims = getattr(request.state, "claims", None)
    
    if claims is None:
        claims = get_authenticated_claims(request)
    
    sub = claims["sub"]

    if TESTING:
        return {
            "sub": sub,
            "given_name": "Test",
            "family_name": "User",
            "custom:role": "admin",
            "custom:neighbourhood_id": None,
        }

    user = (
        db.query(User)
        .filter(User.cognito_sub == sub)
        .first()
    )

    if user is None and not TESTING:
        print("User is none and not os.environ")

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return {
        "sub": sub,
        "given_name": user.first_name,
        "family_name": user.last_name,
        "custom:role": user.role.value,
        "custom:neighbourhood_id": (
            str(user.neighbourhood_id)
            if user.neighbourhood_id
            else None
        ),
    }

def require_role(*allowed_roles: str):#input any number of roles that are allowed and it will check for you
    """Dependency function to check if the current user has one of the allowed roles. If allowed, then will return current user"""
    def role_checker(current_user: dict = Depends(get_current_user)):

        user_role = current_user["custom:role"]

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker