from jose import JWTError, jwt
from fastapi import HTTPException
from app.core.config import config
import httpx
import os
import boto3
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
    
COGNITO_REGION = os.getenv("COGNITO_REGION")
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

#temporarilyy functions to test other things.
#Should ONLY talk to Cognito
def sign_up(email: str, password : str, name : str, address: str):
    try:
        response = client.sign_up(
            ClientId = CLIENT_ID,
            Username = email,
            Password = password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "name", "Value": name},
                {"Name": "address", "Value": address},
            ],
        )

        return { # TODO: Send this response to the database to add the user
            "success": True,
            "user_sub": response["UserSub"],
            "user_confirmed": response["UserConfirmed"],
        }
    except ClientError as e:
        raise Exception({ #TODO: Change to HTTPException
            "success": False,
            "error": e.response["Error"]["Code"],
            "message": e.response["Error"]["Message"]
        })

def login(email, password):
    try:
        response = client.initiate_auth(
            ClientId = CLIENT_ID,
            AuthFlow = "USER_PASSWORD_AUTH",
            AuthParameters = {
                "USERNAME": email,
                "PASSWORD": password,
            },
        )

        auth_result = response["AuthenticationResult"]

        return {
            "access_token": auth_result["AccessToken"],
            "id_token": auth_result["IdToken"],
            "refresh_token": auth_result.get("RefreshToken"),
            "expires_in": auth_result["ExpiresIn"],
            "token_type": auth_result["TokenType"],
        }
    except ClientError as e:
        raise Exception({ #TODO: Change to HTTPException
            "success": False,
            "error": e.response["Error"]["Code"],
            "message": e.response["Error"]["Message"]
        })

def confirm_sign_up(email, code):
    try:
        response = client.confirm_sign_up(
            ClientId = CLIENT_ID,
            Username = email,
            ConfirmationCode = code,
        )

        return{
            "message": "user confirmed",
            "response": response,
        }
    except ClientError as e:
        raise Exception ({#TODO: Change to HTTPException
            "success": False,
            "error": e.response["Error"]["Code"],
            "message": e.response["Error"]["Message"]
        })