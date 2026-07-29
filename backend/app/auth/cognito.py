import jwt
from jwt import algorithms
from fastapi import HTTPException
from app.core.config import config
import httpx
import boto3
from functools import lru_cache
from botocore.exceptions import ClientError

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
                rsa_key = algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], audience=config.cognito_client_id)

        return payload

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
COGNITO_REGION = config.cognito_region
USER_POOL_ID = config.cognito_user_pool_id
CLIENT_ID = config.cognito_client_id

def get_cognito_client():
    return boto3.client(
        "cognito-idp",
        region_name=config.cognito_region
    )

#temporarilyy functions to test other things.
#Should ONLY talk to Cognito
def sign_up(email: str, password : str, name : str, address: str):
    try:
        client = get_cognito_client()
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

        return {
            "success": True,
            "user_sub": response["UserSub"],
            "user_confirmed": response["UserConfirmed"],
        }
    except ClientError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.response["Error"]["Code"],
                "message": e.response["Error"]["Message"]
            }
        )

def login(email, password):
    try:
        client = get_cognito_client()
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
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.response["Error"]["Code"],
                "message": e.response["Error"]["Message"]
            }
        )

def confirm_sign_up(email, code):
    try:
        client = get_cognito_client()
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
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.response["Error"]["Code"],
                "message": e.response["Error"]["Message"]
            }
        )
    
def resend_code(email: str):
    try:
        client = get_cognito_client()
        response = client.resend_confirmation_code(
            ClientId=CLIENT_ID,
            Username=email,
        )
        
        return {
            "message": "New confirmation code sent successfully",
            "response": response
        }
    except ClientError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.response["Error"]["Code"],
                "message": e.response["Error"]["Message"]
            }
        )

def get_sub_from_id_token(id_token: str) -> str:
    payload = verify_token(id_token)
    return payload["sub"]