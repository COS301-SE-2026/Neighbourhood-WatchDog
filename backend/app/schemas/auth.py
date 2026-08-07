from pydantic import BaseModel,EmailStr
from typing import Optional

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
#sign
class SignUpData(BaseModel):
    user_sub: str
    user_confirmed: bool


class SignUpRes(BaseModel):
    success: bool
    data: SignUpData

# Login


class LoginData(BaseModel):
    mfa_required: Optional[bool] = None
    session: Optional[str] = None
    delivery: Optional[dict] = None

    access_token: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None


class LoginRes(BaseModel):
    success: bool
    data: LoginData

# Confirm Signup

class ConfirmSignUpData(BaseModel):
    confirmed: bool


class ConfirmSignUpRes(BaseModel):
    success: bool
    data: ConfirmSignUpData
# Resend Confirmation Code
class ResendCodeData(BaseModel):
    message: str


class ResendCodeRes(BaseModel):
    success: bool
    data: ResendCodeData


# Verify MFA
class VerifyMFAData(BaseModel):
    access_token: str
    id_token: str
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None


class VerifyMFARes(BaseModel):
    success: bool
    data: VerifyMFAData