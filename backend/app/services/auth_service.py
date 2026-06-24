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

    return {
        "success": True,
        "data": {
            "access_token": response["AuthenticationResult"]["AccessToken"],
            "id_token": response["AuthenticationResult"]["IdToken"],
            "refresh_token": response["AuthenticationResult"]["RefreshToken"],
            "token_type": response["AuthenticationResult"]["TokenType"]
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