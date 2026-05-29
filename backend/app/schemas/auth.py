from pydantic import BaseModel,EmailStr

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    address: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ConfirmSignUpRequest(BaseModel):
    email: EmailStr
    code: str