from jose import jwt
from jose.exceptions import JWTError

import requests

from app.core.config import config


JWKS_URL = (f"https://cognito-idp.{config.aws_region}.amazonaws.com/{config.cognito_user_pool_id}/.well-known/jwks.json") #get public keys from AWS to verify
ISSUER = (f"https://cognito-idp.{config.aws_region}.amazonaws.com/{config.cognito_user_pool_id}") #did this JWT come from our user pool

JWKS = requests.get(JWKS_URL).json()["keys"] #public keys for user pool


def verify_jwt(token: str) -> dict:
    headers = jwt.get_unverified_header(token) #decode JWT headers
    kid = headers.get("kid") #key id to find which public key used
    key = next((k for k in JWKS if k["kid"] == kid), None) #find which primary key was used

    if key is None:
        raise JWTError("Unable to find matching public key.")

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