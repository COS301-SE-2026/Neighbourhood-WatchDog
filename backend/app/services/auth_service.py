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

def authenticate_user(email,password):
    return login(email,password)

def confirm_user(email,code):
    return confirm_sign_up(email,code)