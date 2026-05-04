from fastapi import Depends, HTTPException
from app.auth.dependencies import get_current_user

def require_role(allowed_roles: list[str]):
    async def check_role(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("custom:role")

        if not user_role or user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return current_user
