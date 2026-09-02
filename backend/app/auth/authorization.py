from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    CUSTOM_ROLE_CLAIM,
    get_current_user,
)
from app.core.database import DbSession
from app.models.camera import Camera
from app.models.neighbourhood_user import (
    NeighbourhoodRole,
    NeighbourhoodUser,
)
from app.models.property import Property
from app.models.property_user import PropertyUser
from app.models.user import User


AdminPermission = Literal[
    "SYSTEM_ADMIN",
    "PROPERTY_ADMIN",
    "NEIGHBOURHOOD_ADMIN",
]

async def is_property_admin(
    property_id: UUID,
    claims: dict,
    db: AsyncSession,
) -> bool:
    user_sub = claims.get("sub")

    if not user_sub:
        return False

    result = await db.execute(
        select(PropertyUser)
        .join(PropertyUser.user)
        .where(
            PropertyUser.property_id == property_id,
            PropertyUser.is_admin.is_(True),
            User.cognito_sub == user_sub,
        )
    )

    return result.scalar_one_or_none() is not None


async def is_neighbourhood_admin(
    neighbourhood_id: UUID | None,
    claims: dict,
    db: AsyncSession,
) -> bool:
    user_sub = claims.get("sub")

    if not user_sub or neighbourhood_id is None:
        return False

    result = await db.execute(
        select(NeighbourhoodUser)
        .join(NeighbourhoodUser.user)
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            NeighbourhoodUser.role
            == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
            User.cognito_sub == user_sub,
        )
    )

    return result.scalar_one_or_none() is not None