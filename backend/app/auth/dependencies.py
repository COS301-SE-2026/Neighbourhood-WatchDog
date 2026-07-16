from fastapi import HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
from app.auth.jwt import get_authenticated_claims

from app.core.database import get_db
from app.models.user import User

# default mock identity
# TODO: remove mock when Cognito is live
# change these to test different baseline states without touching headers

def get_current_user(request: Request, db: Session = Depends(get_db)):
    claims = getattr(request.state, "claims", None)

    if claims is None:
        claims = get_authenticated_claims(request)
    
    sub = claims["sub"]
    email = claims["email"]

    user = (
        db.query(User)
        .filter(User.cognito_sub == sub)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return {
        "sub": sub,
        "email": email,
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



















# MOCK_SUB = "00000000-0000-0000-0000-000000000001"
# MOCK_EMAIL = "admin@northwood.com"
# MOCK_FIRST_NAME = "Sarah"
# MOCK_LAST_NAME = "Johnson"
# MOCK_ROLE = "NEIGHBOURHOOD_ADMIN"
# MOCK_NEIGHBOURHOOD_ID: str | None = "a1111111-1111-1111-1111-111111111111"

# # mock claims for now, real Cognito later
# async def get_current_user(
#     x_mock_role: str | None = Header(default=None),
#     x_mock_sub: str | None = Header(default=None),
#     x_mock_neighbourhood_id: str | None = Header(default=None),
#     x_mock_email: str | None = Header(default=None),
#     x_mock_first_name: str | None = Header(default=None),
#     x_mock_last_name: str | None = Header(default=None),
# ) -> dict:
#     role = x_mock_role or MOCK_ROLE
#     sub = x_mock_sub or MOCK_SUB
#     neighbourhood_id = x_mock_neighbourhood_id or MOCK_NEIGHBOURHOOD_ID
#     email = x_mock_email or MOCK_EMAIL
#     first_name = x_mock_first_name or MOCK_FIRST_NAME
#     last_name = x_mock_last_name or MOCK_LAST_NAME
 
#     valid_roles = {
#         "RESIDENT",
#         "NEIGHBOURHOOD_ADMIN",
#         "PROP_ADMIN",
#         "SYSTEM_ADMIN",
#     }
#     if role not in valid_roles:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"X-Mock-Role must be one of {sorted(valid_roles)}",
#         )
 
#     try:
#         uuid.UUID(sub)
#     except ValueError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="X-Mock-Sub must be a valid UUID",
#         )
 
#     claims: dict = {
#         "sub": sub,
#         "email": email,
#         "given_name": first_name,
#         "family_name": last_name,
#         "custom:role": role,
#     }

#     # only include neighbourhood_id if it's set
#     if neighbourhood_id:
#         try:
#             uuid.UUID(neighbourhood_id)
#         except ValueError:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="X-Mock-Neighbourhood-Id must be a valid UUID",
#             )
#         claims["custom:neighbourhood_id"] = neighbourhood_id
 
#     return claims
 