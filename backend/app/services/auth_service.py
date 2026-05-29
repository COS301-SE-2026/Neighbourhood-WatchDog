from app.auth.cognito import sign_up, login, confirm_sign_up

def register_user(email,password,name,address):
    return sign_up(email,password,name,address)

def authenticate_user(email,password):
    return login(email,password)

def confirm_user(email,code):
    return confirm_sign_up(email,code)