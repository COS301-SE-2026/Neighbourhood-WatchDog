from fastapi import HTTPException
from app.auth.cognito import sign_up, login, confirm_sign_up, resend_code, get_sub_from_id_token
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import UserRole, User
from sqlalchemy.orm import Session
from sqlalchemy import select


#Business Logic between our API and AWS
#take clean input and calls cognito then reshape results into app format
#Frontend must never rely on AWS naming convention
def register_user(payload, db: Session):
    response = sign_up(
        email=payload["email"],
        password=payload["password"],
        name=payload["firstName"] + " " + payload["lastName"], # combine first and last name to meet the "full name"
        address=payload["address"]
    )

    user_sub = response.get("UserSub", response.get("user_sub"))
    user_confirmed = response.get("UserConfirmed", response.get("user_confirmed"))

    #Add user to db
    new_user = User(
        email=payload["email"],
        first_name=payload["firstName"],
        last_name=payload["lastName"],
        cognito_sub=user_sub,
        role=UserRole.RESIDENT,
        neighbourhood_id=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "data": {
            "user_sub": user_sub,
            "user_confirmed": user_confirmed
        }
    }

def authenticate_user(payload, db: Session):
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

    cognito_sub = get_sub_from_id_token(response["id_token"])

    user = db.execute(select(User).where(User.cognito_sub == cognito_sub)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    properties_stmt = (
        select(Property)
        .join(PropertyUser, PropertyUser.property_id == Property.id)
        .where(PropertyUser.user_id == user.id)
    )
    properties = db.execute(properties_stmt).scalars().all()

    property_data = [
        {
            "id": str(property.id),
            "neighbourhood_id": (
                str(property.neighbourhood_id)
                if property.neighbourhood_id is not None
                else None
            ),
            "address": property.address,
        }
        for property in properties
    ]

    neighbourhood_ids = list(
        dict.fromkeys(
            str(property.neighbourhood_id)
            for property in properties
            if property.neighbourhood_id is not None
        )
    )

    return {
        "success": True,
        "data": {
            "access_token": response["access_token"],
            "id_token": response["id_token"],
            "refresh_token": response.get("refresh_token"),
            "token_type": response.get("token_type"),
            "expires_in": response.get("expires_in"),
            "membership_status": "ACTIVE" if neighbourhood_ids else "NONE",
            "requires_onboarding": len(neighbourhood_ids) == 0,
            "properties": property_data,
            "neighbourhood_ids": neighbourhood_ids
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