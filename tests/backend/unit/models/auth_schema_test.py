import pytest
from pydantic import ValidationError

from backend.app.schemas.auth import ( #
    SignUpRequest,
    LoginRequest,
    ConfirmSignUpRequest,
    ResendCodeRequest,
)

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Password123!"
TEST_NAME = "Zaman"
TEST_ADDRESS = "JHB"
TEST_CODE = "123456"

#Singup
def test_signup_valid(): # Valid signup 
    obj = SignUpRequest(
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
        name=TEST_NAME,
        address=TEST_ADDRESS
    )

    assert obj.email == TEST_EMAIL


def test_signup_missing(): # missing name and address
    with pytest.raises(ValidationError):
        SignUpRequest(
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )

#Login
def test_login_valid(): #valid longin
    obj = LoginRequest(
        email=TEST_EMAIL,
        password=TEST_PASSWORD
    )

    assert obj.email == TEST_EMAIL


def test_login_missing_password(): #missing
    with pytest.raises(ValidationError):
        LoginRequest(
            email=TEST_EMAIL
        )

#confirm signup
def test_confirm_valid():
    obj = ConfirmSignUpRequest(
        email=TEST_EMAIL,
        code=TEST_CODE
    )

    assert obj.code == TEST_CODE


def test_confirm_missing_code(): #invalid
    with pytest.raises(ValidationError):
        ConfirmSignUpRequest(
            email=TEST_EMAIL
        )


#resend
def test_resend_valid():
    obj = ResendCodeRequest(email=TEST_EMAIL)
    assert obj.email == TEST_EMAIL


def test_resend_missing_email():
    with pytest.raises(ValidationError):
        ResendCodeRequest()#send nothin