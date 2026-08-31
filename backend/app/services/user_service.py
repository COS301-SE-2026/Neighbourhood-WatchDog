import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.core.database import DbSession
from app.models.neighbourhood import Neighbourhood
from app.models.neighbourhood_user import NeighbourhoodUser
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User, UserRole
from app.schemas.user import CurrentUserContextRes, CurrentUserNeighbourhood, CurrentUserProperty, CurrentUserSummary, GetUserResSchema

logger = logging.getLogger(__name__)

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
        logger.warning("create_user: email missing")
        raise HTTPException(400, "Email missing. Create user unsuccessful")

    if first_name is None or first_name == "":
        logger.warning("create_user: first name missing for email=%s", email)
        raise HTTPException(400, "First name missing. Create user unsuccessful")

    if last_name is None or last_name == "":
        logger.warning("create_user: last name missing for email=%s", email)
        raise HTTPException(400, "Last name missing. Create user unsuccessful")

    if cognito_sub is None or cognito_sub == "":
        logger.warning("create_user: cognito_sub missing for email=%s", email)
        raise HTTPException(400, "Cognito sub missing. Create user unsuccessful")

    if db is None:
        logger.error("create_user: database session missing")
        raise HTTPException(500, "Database session missing. Create user unsuccessful")

    try:
        logger.debug("create_user: checking whether user already exists for email=%s", email)
        # Make sure that the user does not user already exists
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info(
                "create_user: user already exists with id=%s email=%s",
                existing_user.id,
                email,
            )
            return existing_user

        logger.debug("create_user: creating new resident user for email=%s", email)


        # Resident by default
        #TODO add a proper way to deal with log in as other roles
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            cognito_sub=cognito_sub,
            system_role=UserRole.RESIDENT
        )

        db.add(new_user)
        logger.debug("create_user: user added to session for email=%s", email)
        await db.commit()
        logger.debug("create_user: transaction committed for email=%s", email)
        await db.refresh(new_user)
        logger.debug("create_user: refreshed newly created user id=%s", new_user.id)

        logger.info(
            "create_user: successfully created user id=%s email=%s role=%s",
            new_user.id,
            new_user.email,
            new_user.system_role,
        )

        return new_user

    except IntegrityError:
        logger.exception(
            "create_user: integrity error while creating user email=%s",
            email,
        )
        await db.rollback()
        logger.info("create_user: transaction rolled back for email=%s", email)
        raise HTTPException(status_code=500, detail="Failed to create user")

async def get_user_by_id_handler(
    user_id: UUID,
    db: DbSession,
    claims: dict,
) -> GetUserResSchema:
    """Retrieves the user with the passed in user_id and returns their id, email, cognito sub, role and created_at"""
    logger.info("get_user_by_id: request received for user_id=%s", user_id)
    
    _ = claims
    #TODO: does it make sense for any user to be able to get the info of any other 
    # simply because they have a valid JWT and thus valid claims?
    if not db:
        logger.warning("get_user_by_id: failed to fetch user with user_id=%s due to no database session", user_id)
        raise HTTPException(status_code=500, detail="No database session")

    user = await db.get(User, user_id)
    if not user:
        logger.warning("get_user_by_id: could not fine user with user_id=%s", user_id)
        raise HTTPException(status_code=404, detail="User not found")

    logger.info("get_user_by_id: successfully fetched the user with user_id=%s", user_id)
    return GetUserResSchema(
        id=str(user.id),
        email=user.email,
        cognito_sub=user.cognito_sub,
        role=user.system_role.value if hasattr(user.system_role, "value") else str(user.system_role),
        created_at=user.created_at,
    )

async def get_current_user_context_handler(claims: dict, db: DbSession) -> CurrentUserContextRes:
    """Retrieves the context of a user"""
    user_id = UUID(claims["id"])

    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Authenticated user not found in databse")

    user_summary = CurrentUserSummary(
        id=user_id,
        name=user.first_name + " " + user.last_name,
        system_role=user.system_role
    )

    neighbourhoods_result = await db.execute(
        select(NeighbourhoodUser, Neighbourhood.name)
        .join(Neighbourhood, Neighbourhood.id == NeighbourhoodUser.neighbourhood_id)
        .where(NeighbourhoodUser.user_id == user_id)
    )

    neighbourhood_lookup: dict[UUID, CurrentUserNeighbourhood] = {
        membership.neighbourhood_id: CurrentUserNeighbourhood(
            id=membership.neighbourhood_id,
            name=name,
            role=membership.role,
        )
        for membership, name in neighbourhoods_result.all()
    }

    properties_result = await db.execute(
        select(PropertyUser, Property)
        .join(Property, Property.id == PropertyUser.property_id)
        .where(PropertyUser.user_id == user_id)
    )


    current_properties = [
        CurrentUserProperty(
            id=prop_user.property_id,
            address=property.address,
            neighbourhood=neighbourhood_lookup.get(property.neighbourhood_id),
            is_admin=prop_user.is_admin,
        )
        for prop_user, property in properties_result.all()
    ]

    

    return CurrentUserContextRes(
        user=user_summary,
        properties=current_properties
    )

async def get_current_user_settings_handler(claims: dict, db: DbSession) -> CurrentUserContextRes:
    pass


async def update_current_user_settings_handler(claims: dict, db: DbSession) -> CurrentUserContextRes:
    pass