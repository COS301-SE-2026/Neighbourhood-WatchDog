import jwt
import os
from jwt.algorithms import RSAAlgorithm

import requests
from fastapi import HTTPException, Request

from app.core.config import config
from app.core.app_logging import logging

JWKS_URL = (f"https://cognito-idp.{config.aws_region}.amazonaws.com/{config.cognito_user_pool_id}/.well-known/jwks.json") #get public keys from AWS to verify
ISSUER = (f"https://cognito-idp.{config.aws_region}.amazonaws.com/{config.cognito_user_pool_id}") #did this JWT come from our user pool

# JWKS = requests.get(JWKS_URL, timeout= 7).json()["keys"] #public keys for user pool
#Can possibly cache this data so that we do not have to make a req every time

JWKS: list[dict] | None = None

def get_jwks() -> list[dict]:
    global JWKS

    if JWKS is not None:
        return JWKS

    try:
        response = requests.get(JWKS_URL, timeout=7)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise jwt.PyJWTError("Unable to retreive Cognito signing keys.") from exc

    keys = payload.get("keys")
    if not isinstance(keys, list):
        raise jwt.PyJWTError("Cognito JWKS response does not contain a valid 'keys' list.")

    JWKS = keys
    return JWKS

def verify_jwt(token: str) -> dict:
    """Verify a Cognito access token issued for the WatchDog app client."""
    if not config.cognito_client_id:
        raise jwt.PyJWTError("Cognito app client ID is not configured.")

    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")

    if not isinstance(kid, str) or not kid:
        raise jwt.PyJWTError("Token is missing a valid signing key ID.")

    jwks = get_jwks()
    jwk = next((key for key in jwks if key.get("kid") == kid), None)

    if jwk is None:
        raise jwt.PyJWTError("Unable to find matching public key.")

    key = RSAAlgorithm.from_jwk(jwk)

    claims = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        leeway=30,
        issuer=ISSUER,
        options={
            # Cognito access tokens identify the app client with client_id.
            # Validate that claim explicitly below instead of using aud.
            "verify_aud": False,
            "require": [
                "exp",
                "iss",
                "sub",
                "token_use",
                "client_id",
            ],
        },
    )

    if claims["token_use"] != "access":
        raise jwt.InvalidTokenError("An access token is required.")

    if claims["client_id"] != config.cognito_client_id:
        raise jwt.InvalidAudienceError(
            "Token was not issued for the WatchDog app client."
        )

    return claims


def get_authenticated_claims(request: Request) -> dict: #Send JWT to verify_jwt 
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
    except jwt.PyJWTError as e:
        logging.warning("JWT validation failed: %s", e)
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    request.state.claims = claims

    return claims