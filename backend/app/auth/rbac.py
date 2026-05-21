import os
from fastapi import HTTPException

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def require_role(claims: dict, allowed_roles: list[str]) -> None:
    if DEBUG:
        return
    if claims.get("custom:role") is None:
        return
    user_role = claims.get("custom:role") if claims else None
    if not user_role or user_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

def require_neighbourhood_member(claims: dict) -> None:
    if DEBUG:
        return
    if not claims or not claims.get("custom:neighbourhood_id"):
        raise HTTPException(status_code=403, detail="User is not a neighbourhood member")