from fastapi import APIRouter
from app.schemas.auth import ( #Check payloads from schemas
    SignUpRequest,
    LoginRequest,
    ConfirmSignUpRequest,
    ResendCodeRequest
)

from app.services.auth_service import ( #use services
    register_user,
    authenticate_user,
    confirm_user,
    resend_confirmation_code,
)


def _payload_to_dict(payload):
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload.dict()

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
    return register_user(_payload_to_dict(payload))

@router.post("/login")
def login(payload: LoginRequest):
    return authenticate_user(_payload_to_dict(payload))

@router.post("/confirm")
def confirm(payload: ConfirmSignUpRequest):
    return confirm_user(_payload_to_dict(payload))

@router.post("/resend-code")
def resend_code(payload: ResendCodeRequest):
    return resend_confirmation_code(_payload_to_dict(payload))
