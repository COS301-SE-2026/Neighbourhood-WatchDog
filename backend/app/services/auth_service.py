from app.auth.cognito import sign_up, login, confirm_sign_up


#Business Logic between our API and AWS
#take clean input and calls cognito then reshape results into app format
#Frontend must never rely on AWS naming convention
def register_user(payload):
    result = sign_up(
        email = payload.email,
        password = payload.password,
        name = payload.name,
        address = payload.address
    )
    return {
        "user_sub": result["user_sub"],
        "confirmed": result["user_confirmed"]
    }

def authenticate_user(payload):
    result = login(
        email = payload.email,
        password = payload.password
    )

    return {
        "access_token": result["access_token"],
        "id_token": result["id_token"],
        "expires_in": result["expires_in"]
    }

def confirm_user(payload):
    result = confirm_sign_up(
        email = payload.email,
        code = payload.code
    )

    return {
        "confirmed": True,
        "result": result
    }