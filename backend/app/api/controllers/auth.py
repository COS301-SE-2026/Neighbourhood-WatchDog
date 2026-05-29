from fastapi import APIRouter, Depends, Response
from app.services.auth_service import (register_user,authenticate_user,confirm_user)
from app.auth.dependencies import get_current_user

from fastapi import APIRouter
from app.schemas.auth import (
    SignUpRequest,
    LoginRequest,
    ConfirmSignUpRequest
)

from app.services.auth_service import (
    register_user,
    authenticate_user,
    confirm_user
)

router = APIRouter(prefix="/auth", tags=["auth"])
# Need to define the route here and then delegate the work to other layers

#Health check, see if this route is all good
@router.get("/ping")
def auth_ping():
    return{
        "status":"ok",
        "message":"auth router is ALIVE"
    }

@router.post("/signup")
def signup(payload: SignUpRequest):
    return register_user(payload)

@router.post("/login")
def login(payload: LoginRequest):
    return authenticate_user(payload)
