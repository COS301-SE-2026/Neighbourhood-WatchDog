import jwt
import os
from jwt.algorithms import RSAAlgorithm

import requests
from fastapi import HTTPException, Request

from app.core.config import config


JWKS_URL = (f"https://cognito-idp.{config.aws_region}.amazonaws.com/{config.cognito_user_pool_id}/.well-known/jwks.json") #get public keys from AWS to verify
ISSUER = (f"https://cognito-idp.{config.aws_region}.amazonaws.com/{config.cognito_user_pool_id}") #did this JWT come from our user pool

JWKS = requests.get(JWKS_URL, timeout= 7).json()["keys"] #public keys for user pool
#Can possibly cache this data so that we do not have to make a req every time

def verify_jwt(token: str) -> dict:
    """Verifies the JWT and returns the claims (data from JWT)"""
    headers = jwt.get_unverified_header(token) #decode JWT headers
    kid = headers.get("kid") #key id to find which public key used
    jwk = next((k for k in JWKS if k["kid"] == kid), None) #find which primary key was used

    if jwk is None:
        raise jwt.PyJWTError("Unable to find matching public key.")

    key = RSAAlgorithm.from_jwk(jwk)

    claims = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        issuer=ISSUER,
        options={
            "verify_aud": False
        },
    )

    return claims


def get_authenticated_claims(request: Request) -> dict:
    TESTING = os.environ.get("TESTING", "false").lower() == "true"
    if TESTING:
        return {
            "sub": "00000000-0000-0000-0000-000000000001",
            "given_name": "Test",
            "family_name": "User",
            "custom:role": "admin",
            "custom:neighbourhood_id": None,
        }

    """Extracts JWT verifies it stores the claims on request.state and returns claims(Data from JWT)"""

    # Already authenticated?
    claims = getattr(request.state, "claims", None)
    if claims is not None:
        return claims

    auth_header = request.headers.get("Authorization")#Check authorization header exists

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    if not auth_header.startswith("Bearer "): #Does it have bearer JWT token
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header",
        )

    token = auth_header.split(" ", 1)[1] #Get actual JWT

    try:
        claims = verify_jwt(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    request.state.claims = claims

    return claims