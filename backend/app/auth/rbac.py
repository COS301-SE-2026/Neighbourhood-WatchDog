from fastapi import HTTPException

def require_role(claims: dict, allowed_roles: list[str]) -> None:
    user_role = claims.get("custom:role") if claims else None
    if not user_role or user_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

def require_neighbourhood_member(claims: dict) -> None:
    if not claims or not claims.get("custom:neighbourhood_id"):
        raise HTTPException(status_code=403, detail="User is not a neighbourhood member")