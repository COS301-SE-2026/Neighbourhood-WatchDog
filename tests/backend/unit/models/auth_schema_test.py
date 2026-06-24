import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.app.schemas.auth import ( #
    SignUpRequest,
    LoginRequest,
    ConfirmSignUpRequest,
    ResendCodeRequest,
)
#Singup
def test_signup_valid(): # Valid signup 
    obj = SignUpRequest(
        email="test@example.com",
        password="Password123!",
        name="Zaman",
        address="JHB"
    )

    assert obj.email == "test@example.com"


def test_signup_missing(): # missing name and address
    with pytest.raises(ValidationError):
        SignUpRequest(
            email="test@example.com",
            password="Password123!"
        )

#Login
def test_login_valid(): #valid longin
    obj = LoginRequest(
        email="test@example.com",
        password="Password123!"
    )

    assert obj.email == "test@example.com"


def test_login_missing_password(): #missing
    with pytest.raises(ValidationError):
        LoginRequest(
            email="test@example.com"
        )

#confirm signup
def test_confirm_valid():
    obj = ConfirmSignUpRequest(
        email="test@example.com",
        code="123456"
    )

    assert obj.code == "123456"


def test_confirm_missing_code(): #invalid
    with pytest.raises(ValidationError):
        ConfirmSignUpRequest(
            email="test@example.com"
        )


#resend
def test_resend_valid():
    obj = ResendCodeRequest(email="test@example.com")
    assert obj.email == "test@example.com"


def test_resend_missing_email():
    with pytest.raises(ValidationError):
        ResendCodeRequest()#send nothin