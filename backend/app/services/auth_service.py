from fastapi import HTTPException
from app.auth.cognito import sign_up, login, confirm_sign_up, resend_code


#Business Logic between our API and AWS
#take clean input and calls cognito then reshape results into app format
#Frontend must never rely on AWS naming convention
def register_user(payload):
    response = sign_up(
        email=payload["email"],
        password=payload["password"],
        name=payload["name"],
        address=payload["address"]
    )

    return {
        "success": True,
        "data": {
            "user_sub": response["UserSub"],
            "user_confirmed": response["UserConfirmed"]
        }
    }

def authenticate_user(payload):
    response = login(
        email=payload["email"],
        password=payload["password"]
    )

    if not response.get("access_token") or not response.get("id_token"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AuthenticationFailed",
                "message": response,
            },
        )

    return {
        "success": True,
        "data": {
            "access_token": response["access_token"],
            "id_token": response["id_token"],
            "refresh_token": response.get("refresh_token"),
            "token_type": response.get("token_type"),
            "expires_in": response.get("expires_in"),
        }
    }

def confirm_user(payload):
    response = confirm_sign_up(
        email=payload["email"],
        code=payload["code"]
    )

    return {
        "success": True,
        "data": {
            "status": response["status"]
        }
    }

def resend_confirmation_code(payload):
    response = resend_code(payload["email"])

    return {
        "success": True,
        "data": {
            "message": response.get("message", "sent")
        }
    }