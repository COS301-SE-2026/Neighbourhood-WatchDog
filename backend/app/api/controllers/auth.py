from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.services.user_service import create_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: DbSession = None
):
    """Get current user info and create in database if needed"""
    user = await create_user(
        email=current_user.get("email"),
        first_name=current_user.get("given_name", ""),
        last_name=current_user.get("family_name", ""),
        cognito_sub=current_user.get("sub"),
        db=db
    )
    return user

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint"""
    return {"message": "Logged out"}

