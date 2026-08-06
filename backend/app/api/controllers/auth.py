from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from typing import Annotated

from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.services.user_service import create_user
from app.models.user import User
from app.auth.rate_limiter import limiter

from app.schemas.auth import ( #Check payloads from schemas
    SignUpRequest,
    LoginRequest,
    ConfirmSignUpRequest,
    ResendCodeRequest,
    VerifyMFARequest
)

from app.services.auth_service import ( #use services
    register_user,
    authenticate_user,
    confirm_user,
    resend_confirmation_code,
    complete_mfa
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
@limiter.limit("3/minute")  # Limit to 3 requests per minute
async def signup(request: Request, payload: SignUpRequest, db: DbSession):
    return await register_user(_payload_to_dict(payload), db)

@router.post("/login")
@limiter.limit("5/minute")  # Limit to 5 requests per minute
async def login(request: Request, payload: LoginRequest):
    return await authenticate_user(_payload_to_dict(payload))

@router.post("/confirm")
@limiter.limit("15/minute")  # Limit to 15 requests per minute
async def confirm(request: Request, payload: ConfirmSignUpRequest):
    return await confirm_user(_payload_to_dict(payload))


@router.get("/me", responses={401: {"description" : "Invalid token claims or user not found"}})
@limiter.limit("10/minute")  # Limit to 10 requests per minute
async def get_current_user_info(
    request: Request,
    db: DbSession,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get current user info and create in database if needed"""
    cognito_sub = current_user.get("sub")

    print(cognito_sub)
    
    if not cognito_sub:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    stmt = select(User).where(User.cognito_sub == cognito_sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

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

@router.post("/resend-code")
@limiter.limit("10/minute")  # Limit to 10 requests per minute
async def resend_code(request: Request, payload: ResendCodeRequest):
    return await resend_confirmation_code(_payload_to_dict(payload))

@router.post("/verify-mfa")
@limiter.limit("10/minute")
async def verify_mfa(request: Request, payload: VerifyMFARequest):
    return await complete_mfa(_payload_to_dict(payload))