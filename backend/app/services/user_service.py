from fastapi import HTTPException
from app.core.database import DbSession
from sqlalchemy import select
from app.models.user import User, UserRole
from sqlalchemy.exc import IntegrityError


async def create_user(
    email: str,
    first_name: str,
    last_name: str,
    cognito_sub: str,
    db: DbSession
) -> User:
    """Create a new user in the database with RESIDENT role"""

    # explanation of this function and its need as opposed to regular sign up:
    # instead of using a signup endpoint we just finna receive the claims 
    # in each req and it'll run this everytime get_current_user is called
    # so pretty much on every protected endpoint
    # that way if the user does not already exist they will be created 

    if email is None or email == "":
        raise HTTPException(400, "Email missing. Create user unsuccessful")

    if first_name is None or first_name == "":
        raise HTTPException(400, "First name missing. Create user unsuccessful")

    if last_name is None or last_name == "":
        raise HTTPException(400, "Last name missing. Create user unsuccessful")

    if cognito_sub is None or cognito_sub == "":
        raise HTTPException(400, "Cognito sub missing. Create user unsuccessful")

    if db is None:
        raise HTTPException(500, "Database session missing. Create user unsuccessful")

    try:
        # Make sure that the user does not user already exists
        stmt = select(User).where(User.email == email)
        existing_user = db.execute(stmt).scalar_one_or_none()

        if existing_user:
            return existing_user

        # Resident by default
        #TODO add a proper way to deal with log in as other roles
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            cognito_sub=cognito_sub,
            role=UserRole.RESIDENT
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")