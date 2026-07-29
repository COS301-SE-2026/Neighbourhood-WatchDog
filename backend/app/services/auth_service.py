from fastapi import HTTPException
from app.auth.cognito import sign_up, login, confirm_sign_up, resend_code
from app.models.user import UserRole, User
from sqlalchemy.orm import Session

from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction

#Business Logic between our API and AWS
#take clean input and calls cognito then reshape results into app format
#Frontend must never rely on AWS naming convention
def register_user(payload, db: Session):
    response = sign_up(
        email=payload["email"],
        password=payload["password"],
        name=payload["firstName"] + " " + payload["lastName"],
        address=payload["address"]
    )

    user_sub = response.get("UserSub", response.get("user_sub"))
    user_confirmed = response.get("UserConfirmed", response.get("user_confirmed"))

    new_user = User(
        email=payload["email"],
        first_name=payload["firstName"],
        last_name=payload["lastName"],
        cognito_sub=user_sub,
        role=UserRole.RESIDENT,
        neighbourhood_id=None
    )
    db.add(new_user)

    # Generate ID before audit entry
    db.flush()

    create_audit_log_item(
        db=db,
        user_id=new_user.id,
        action=AuditAction.CREATE,
        target_entity_type="User",
        target_entity_id=new_user.id,
        new_values={
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "role": new_user.role.value,
            "neighbourhood_id": (
                str(new_user.neighbourhood_id)
                if new_user.neighbourhood_id
                else None
            ),
        },
    )
    db.commit()

    return {
        "success": True,
        "data": {
            "user_sub": user_sub,
            "user_confirmed": user_confirmed
        }
    }

def authenticate_user(payload):
    response = login(
        email=payload["email"],
        password=payload["password"]
    )

    if not response.get("access_token") or not response.get("id_token"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AuthenticationFailed",
                "message": response,
            },
        )

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

def confirm_user(payload):
    confirm_sign_up(
        email=payload["email"],
        code=payload["code"]
    )

    return {
        "success": True,
        "data": {
            "confirmed": True
        }
    }

def resend_confirmation_code(payload):
    response = resend_code(payload["email"])

    return {
        "success": True,
        "data": {
            "message": response.get("message", "sent")
        }
    }