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

async def is_property_member(
    property_id: UUID,
    claims: dict,
    db: AsyncSession,
) -> bool:
    """
    Check whether the authenticated user belongs to the specified property.

    Use this for property-scoped read operations where normal property
    members are allowed to view the resource.

    This function returns False when the user is not a member.
    It does not raise an HTTP exception by itself.
    """

    if not claims:
        return False

    user_sub = claims.get("sub")

    if not user_sub:
        return False

    result = await db.execute(
        select(PropertyUser)
        .join(PropertyUser.user)
        .where(
            PropertyUser.property_id == property_id,
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

async def is_neighbourhood_member(
    neighbourhood_id: UUID,
    claims: dict,
    db: AsyncSession,
) -> bool:
    """
    Check whether the authenticated user belongs to the specified
    neighbourhood.

    This checks for any NeighbourhoodUser membership record.
    The user's neighbourhood role may be:

        - RESIDENT
        - NEIGHBOURHOOD_ADMIN
        - SECURITY_OFFICER

    Use this for neighbourhood-scoped read operations where all members
    are allowed to view the resource.

    This function returns False when the user is not a member.
    It does not raise an HTTP exception by itself.
    """

    if not claims:
        return False

    user_sub = claims.get("sub")

    if not user_sub or neighbourhood_id is None:
        return False

    result = await db.execute(
        select(NeighbourhoodUser)
        .join(NeighbourhoodUser.user)
        .where(
            NeighbourhoodUser.neighbourhood_id == neighbourhood_id,
            User.cognito_sub == user_sub,
        )
    )

    return result.scalar_one_or_none() is not None

async def _has_required_permission(
    required_permissions: tuple[AdminPermission, ...],
    property_id: UUID,
    neighbourhood_id: UUID | None,
    claims: dict,
    db: AsyncSession,
) -> bool:
    """"Check if the user has the required permissions based on their role and the provided property or neighbourhood ID."""
    current_role = claims.get(CUSTOM_ROLE_CLAIM)

    if (
        "SYSTEM_ADMIN" in required_permissions
        and current_role == "SYSTEM_ADMIN"
    ):
        return True

    if "PROPERTY_ADMIN" in required_permissions:
        if await is_property_admin(
            property_id,
            claims,
            db,
        ):
            return True

    if "NEIGHBOURHOOD_ADMIN" in required_permissions:
        if await is_neighbourhood_admin(
            neighbourhood_id,
            claims,
            db,
        ):
            return True

    return False

def require_property_authorization(
    *required_permissions: AdminPermission,
):
    async def checker(
        property_id: UUID,
        db: DbSession,
        claims: Annotated[
            dict,
            Depends(get_current_user),
        ],
    ) -> dict:
        property_result = await db.execute(
            select(Property).where(
                Property.id == property_id,
            )
        )

        property_obj = property_result.scalar_one_or_none()

        if property_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found",
            )

        allowed = await _has_required_permission(
            required_permissions=required_permissions,
            property_id=property_obj.id,
            neighbourhood_id=property_obj.neighbourhood_id,
            claims=claims,
            db=db,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to manage this property"
                ),
            )

        return claims

    return checker

def require_camera_authorization(
    *required_permissions: AdminPermission,
):
    async def checker(
        camera_id: UUID,
        db: DbSession,
        claims: Annotated[
            dict,
            Depends(get_current_user),
        ],
    ) -> dict:
        camera_result = await db.execute(
            select(Camera).where(
                Camera.id == camera_id,
            )
        )

        camera = camera_result.scalar_one_or_none()

        if camera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found",
            )

        property_result = await db.execute(
            select(Property).where(
                Property.id == camera.property_id,
            )
        )

        property_obj = property_result.scalar_one_or_none()

        if property_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera property not found",
            )

        allowed = await _has_required_permission(
            required_permissions=required_permissions,
            property_id=property_obj.id,
            neighbourhood_id=property_obj.neighbourhood_id,
            claims=claims,
            db=db,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to manage this camera"
                ),
            )

        return claims

    return checker

def require_neighbourhood_authorization(
    *required_permissions: AdminPermission,
):
    async def checker(
        neighbourhood_id: UUID,
        db: DbSession,
        claims: Annotated[
            dict,
            Depends(get_current_user),
        ],
    ) -> dict:
        current_role = claims.get(CUSTOM_ROLE_CLAIM)

        if (
            "SYSTEM_ADMIN" in required_permissions
            and current_role == "SYSTEM_ADMIN"
        ):
            return claims

        allowed = False

        if "NEIGHBOURHOOD_ADMIN" in required_permissions:
            result = await db.execute(
                select(NeighbourhoodUser)
                .join(NeighbourhoodUser.user)
                .where(
                    NeighbourhoodUser.neighbourhood_id
                    == neighbourhood_id,
                    NeighbourhoodUser.role
                    == NeighbourhoodRole.NEIGHBOURHOOD_ADMIN,
                    User.cognito_sub == claims.get("sub"),
                )
            )

            allowed = result.scalar_one_or_none() is not None

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to manage this neighbourhood"
                ),
            )

        return claims

    return checker