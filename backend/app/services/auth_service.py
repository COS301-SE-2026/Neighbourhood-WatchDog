from fastapi import HTTPException
from app.auth.cognito import sign_up, login, confirm_sign_up, resend_code, respond_to_mfa
from app.models.user import UserRole, User
import asyncio
from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction, TargetEntity

#Business Logic between our API and AWS
#take clean input and calls cognito then reshape results into app format
#Frontend must never rely on AWS naming convention
import logging

logger = logging.getLogger(__name__)

async def register_user(payload, db):
    """Register a local user and Cognito account from the supplied signup details."""    
    response = await asyncio.to_thread(
        sign_up,
        email=payload["email"],
        password=payload["password"],
        name=payload["firstName"] + " " + payload["lastName"],
        address=payload["address"]
    )

    user_sub = response.get("UserSub", response.get("user_sub"))
    user_confirmed = response.get("UserConfirmed", response.get("user_confirmed"))

    try:
        new_user = User(
            email=payload["email"],
            first_name=payload["firstName"],
            last_name=payload["lastName"],
            cognito_sub=user_sub,
            system_role=UserRole.RESIDENT,
        )
        db.add(new_user)

        logger.info("User registration completed: user_id=%s", new_user.id)
    
        # Generate ID before audit entry
        await db.flush()
    
        create_audit_log_item(
            db=db,
            user_id=new_user.id,
            action=AuditAction.CREATE,
            target_entity_type=TargetEntity.USER,
            target_entity_id=new_user.id,
            new_values={
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "role": new_user.system_role.value,
                "neighbourhood_id": (
                    str(new_user.neighbourhood_id)
                    if new_user.neighbourhood_id
                    else None
                ),
            },
        )
        await db.commit()
    except Exception:
        await db.rollback()

        logger.warning(
            "Authentication rejected because no local user profile exists"
        )
        raise

    return {
        "success": True,
        "data": {
            "user_sub": user_sub,
            "user_confirmed": user_confirmed
        }
    }

async def authenticate_user(payload):
    """Authenticate a user with Cognito and return the authentication result."""
    response = await asyncio.to_thread(
        login,
        email=payload["email"],
        password=payload["password"]
    )
    if response.get("challenge"): #This tells us that Cognito requires MFA
        challenge = response.get("challenge")
        if challenge == "EMAIL_OTP":# check if the challenge sent back is actually OTP
            return {
                "success": True,
                "data": {
                    "mfa_required": True,
                    "session": response["session"],
                    "delivery": response.get("delivery"),
                },
            }

    if response.get("access_token"): # Login successfull (MFA not needed)
        return {
            "success": True,
            "data": {
                "access_token": response["access_token"],
                "id_token": response["id_token"],
                "refresh_token": response.get("refresh_token"),
                "token_type": response.get("token_type"),
                "expires_in": response.get("expires_in"),
            }
        }

    logger.exception("Cognito authentication operation failed unexpectedly")

    raise HTTPException( #Did not get expected values
        status_code=400,
        detail={
            "error": "AuthenticationFailed",
            "message": response,
        },
        
    )
    

async def confirm_user(payload):
    """Confirm a user's Cognito account using the supplied verification code."""
    await asyncio.to_thread(
        confirm_sign_up,
        email=payload["email"],
        code=payload["code"]
    )

    return {
        "success": True,
        "data": {
            "confirmed": True
        }
    }

async def resend_confirmation_code(payload):
    """Request that Cognito resend an account confirmation code to the user."""
    response = await asyncio.to_thread(
        resend_code,
        payload["email"]
    )

    return {
        "success": True,
        "data": {
            "message": response.get("message", "sent")
        }
    }

async def complete_mfa(payload):
    """Complete a Cognito multi-factor authentication challenge."""
    response = await asyncio.to_thread(
        respond_to_mfa,
        email=payload["email"],
        session=payload["session"],
        code=payload["code"],
    )

    return {#If an error with cognito occurs the "response" variable will throw an error 
        "success": True,
        "data": {
            "access_token": response["access_token"],
            "id_token": response["id_token"],
            "refresh_token": response.get("refresh_token"),
            "token_type": response.get("token_type"),
            "expires_in": response.get("expires_in"),
        },
    }