from pydantic import BaseModel,EmailStr

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    address: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ConfirmSignUpRequest(BaseModel):
    email: EmailStr
    code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr

class VerifyMFARequest(BaseModel):
    email: EmailStr
    session: str
    code: str