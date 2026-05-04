from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(email: str, password: str):
    """Login endpoint - returns JWT token from Cognito"""
    # Call Cognito AdminInitiateAuth or InitiateAuth
    # Return token to client
    pass

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh expired JWT token"""
    # Call Cognito InitiateAuth with REFRESH_TOKEN_AUTH flow
    pass

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info from token claims"""
    return current_user

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint"""
    return {"message": "Logged out"}