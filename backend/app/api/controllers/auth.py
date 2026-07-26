from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.services.user_service import create_user
from app.models.user import User
from fastapi import APIRouter, Request
from app.auth.rate_limiter import limiter

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
@limiter.limit("3/minute")  # Limit to 5 requests per minute
def signup(payload: SignUpRequest):
    return register_user(_payload_to_dict(payload))

@router.post("/login")
@limiter.limit("5/minute")  # Limit to 5 requests per minute
def login(payload: LoginRequest):
    return authenticate_user(_payload_to_dict(payload))

@router.post("/confirm")
@limiter.limit("15/minute")  # Limit to 3 requests per minute
def confirm(payload: ConfirmSignUpRequest):
    return confirm_user(_payload_to_dict(payload))


@router.get("/me", responses={401: {"description" : "Invalid token claims or user not found"}})
@limiter.limit("10/minute")  # Limit to 10 requests per minute
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: DbSession = None
):
    """Get current user info and create in database if needed"""
    cognito_sub = current_user.get("sub")

    print(cognito_sub)
    
    if not cognito_sub:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    stmt = select(User).where(User.cognito_sub == cognito_sub)
    user =  db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    email = user.email

    user_output = await create_user(
        email=email,
        first_name=current_user.get("given_name", ""),
        last_name=current_user.get("family_name", ""),
        cognito_sub=cognito_sub,
        db=db
    )
    return user_output

@router.post("/logout")
@limiter.limit("10/minute")  # Limit to 10 requests per minute
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint"""
    return {"message": "Logged out"}

@router.post("/resend-code")
@limiter.limit("10/minute")  # Limit to 10 requests per minute
def resend_code(payload: ResendCodeRequest):
    return resend_confirmation_code(_payload_to_dict(payload))