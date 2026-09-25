from uuid import UUID
from sqlalchemy import select

from app.core.database import DbSession
from app.models.neighbourhood_user import NeighbourhoodRole, NeighbourhoodUser
from app.models.property_user import PropertyUser
from app.models.property import Property
from app.models.user import User

async def resolve_neighbourhood_members(db: DbSession, event_context: dict) -> list[User]:
    """Every member of the neighbourhood, any role"""
    neighbourhood_id: UUID = event_context["neighbourhood_id"]

    result = await db.execute(
        select(User)
        .join(NeighbourhoodUser, NeighbourhoodUser.user_id == User.id)
        .where(NeighbourhoodUser.neighbourhood_id == neighbourhood_id)
    )
    return list(result.scalars().all())


async def resolve_neighbourhood_residents(db: DbSession, event_context: dict) -> list[User]:
    """Residents only"""
    neighbourhood_id: UUID = event_context["neighbourhood_id"]

    result = await db.execute(
        select(User)
        .join(NeighbourhoodUser, NeighbourhoodUser.user_id == User.id)
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            NeighbourhoodUser.role == NeighbourhoodRole.RESIDENT,
        )
    )
    return list(result.scalars().all())


async def resolve_neighbourhood_admins(db: DbSession, event_context: dict) -> list[User]:
    """Neighbourhood admins only"""
    neighbourhood_id: UUID = event_context["neighbourhood_id"]

    result = await db.execute(
        select(User)
        .join(NeighbourhoodUser, NeighbourhoodUser.user_id == User.id)
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            NeighbourhoodUser.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
        )
    )
    return list(result.scalars().all())

async def resolve_neighbourhood_officers(db: DbSession, event_context: dict) -> list[User]:
    """Officers only"""
    neighbourhood_id: UUID = event_context["neighbourhood_id"]

    result = await db.execute(
        select(User)
        .join(NeighbourhoodUser, NeighbourhoodUser.user_id == User.id)
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            NeighbourhoodUser.role == NeighbourhoodRole.SECURITY_OFFICER,
        )
    )
    return list(result.scalars().all())

async def resolve_neighbourhood_admins_and_officers(db: DbSession, event_context: dict) -> list[User]:
    """Officers and Neighbourhood admins"""
    neighbourhood_id: UUID = event_context["neighbourhood_id"]

    result = await db.execute(
        select(User)
        .join(NeighbourhoodUser, NeighbourhoodUser.user_id == User.id)
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            NeighbourhoodUser.role == NeighbourhoodRole.SECURITY_OFFICER 
                or NeighbourhoodUser.role == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
        )
    )
    return list(result.scalars().all())

async def resolve_property_members(db: DbSession, event_context: dict) -> list[User]:
    """Returns the users in a property"""
    property_id: UUID = event_context["property_id"]

    result = await db.execute(
        select(User)
        .join(PropertyUser)
        .where(
            NeighbourhoodUser.property_id == property_id
        )
    )
    return list(result.scalars().all())

async def resolve_neighbourhood_admins_officers_and_property_users(db: DbSession, event_context: dict) -> list[User]:
    """Officers and Neighbourhood admins and the users in a property"""
    list1 = await resolve_property_members(db, event_context)
    list2 = await resolve_neighbourhood_admins_and_officers(db, event_context)

    return (list1.append(list2))

async def resolve_users_by_id(db: DbSession, event_context: dict) -> list[User]:
    """For policies handed pre-resolved ids"""
    user_ids: list[UUID] = event_context["user_ids"]

    result = await db.execute(select(User).where(User.id.in_(set(user_ids))))
    return list(result.scalars().all())


async def resolve_single_user(db: DbSession, event_context: dict) -> list[User]:
    """For single-recipient events"""
    user_id: UUID = event_context["user_id"]

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return [user] if user else []