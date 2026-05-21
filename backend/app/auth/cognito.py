from jose import JWTError, jwt
from jose.exceptions import JWTClaimsError
from fastapi import HTTPException
from app.core.config import config
import httpx
from functools import lru_cache

@lru_cache(maxsize=1)
def get_jwks():
    """Fetch and cache the JWKS from Cognito"""
    url = f"https://cognito-idp.{config.cognito_region}.amazonaws.com/{config.cognito_user_pool_id}/.well-known/jwks.json"
    response = httpx.get(url)
    return response.json()

def verify_token(token: str) -> dict:
    """Verify JWT token and return decoded claims"""
    if config.debug and token == "mocktoke":
        return {"sub": "dev-user", "cognito:username": "dev-user", "email": "dev@example.com"}

    try:
        unverified_header = jwt.get_unverified_header(token)

        jwks = get_jwks()

        rsa_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = key
                break

        if not rsa_key:
            raise HTTPException(status=401, detail="Invalid token")

        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], audience=config.cognito_client_id)

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")