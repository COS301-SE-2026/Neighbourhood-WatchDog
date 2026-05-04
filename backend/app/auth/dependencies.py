from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from app.auth.cognito import verify_token

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)) -> dict:
    """Extract and verify JWT, return user claims"""
    token = credentials.credentials
    claims = verify_token(token)
    return claims