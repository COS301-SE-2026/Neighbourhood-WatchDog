from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.neighbourhood import (
    create_neighbourhood,
    get_neighbourhood_members,
    get_neighbourhood_properties,
    update_neighbourhood_member_role,
)
from app.models.neighbourhood_user import NeighbourhoodRole
from app.schemas.neighbourhood import (
    CreateNeighbourhoodReq,
    NeighbourhoodMemberRes,
    NeighbourhoodPropertyRes,
    NeighbourhoodRes,
    UpdateMemberRoleReq,
    UpdateMemberRoleRes,
)


PROPERTY_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()
MEMBER_USER_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_neighbourhood():
    return NeighbourhoodRes(
        id=NEIGHBOURHOOD_ID,
        name="Test Neighbourhood",
        location="Pretoria",
        join_code="ABC123",
        created_at=CREATED_AT,
    )


def make_property():
    return NeighbourhoodPropertyRes(
        id=PROPERTY_ID,
        address="123 Test Street",
        property_type="PRIVATE",
        neighbourhood_id=NEIGHBOURHOOD_ID,
        neighbourhood_name="Test Neighbourhood",
    )


def make_member():
    return NeighbourhoodMemberRes(
        user_id=MEMBER_USER_ID,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        role=NeighbourhoodRole.RESIDENT,
    )


@pytest.mark.asyncio
async def test_create_neighbourhood_checks_property_admin_and_delegates():
    payload = CreateNeighbourhoodReq(
        name="Test Neighbourhood",
        location="Pretoria",
        property_id=PROPERTY_ID,
    )
    expected = make_neighbourhood()

    with patch(
        "app.api.controllers.neighbourhood.is_property_admin",
        new=AsyncMock(return_value=True),
    ) as is_admin, patch(
        "app.api.controllers.neighbourhood.create_neighbourhood_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await create_neighbourhood(payload, DB, CLAIMS)

    assert response.status == 201
    assert response.message == "Neighbourhood created successfully"
    assert response.data == expected

    is_admin.assert_awaited_once_with(PROPERTY_ID, CLAIMS, DB)
    handler.assert_awaited_once_with(
        name=payload.name,
        location=payload.location,
        property_id=payload.property_id,
        db=DB,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_create_neighbourhood_rejects_non_property_admin():
    payload = CreateNeighbourhoodReq(
        name="Test Neighbourhood",
        location="Pretoria",
        property_id=PROPERTY_ID,
    )

    with patch(
        "app.api.controllers.neighbourhood.is_property_admin",
        new=AsyncMock(return_value=False),
    ) as is_admin, patch(
        "app.api.controllers.neighbourhood.create_neighbourhood_handler",
        new=AsyncMock(),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await create_neighbourhood(payload, DB, CLAIMS)

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "You do not have permission to create a neighbourhood for this property"
    )
    is_admin.assert_awaited_once_with(PROPERTY_ID, CLAIMS, DB)
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_neighbourhood_propagates_service_error():
    payload = CreateNeighbourhoodReq(
        name="Test Neighbourhood",
        location="Pretoria",
        property_id=PROPERTY_ID,
    )
    error = HTTPException(
        status_code=400,
        detail="No neighbourhood location given",
    )

    with patch(
        "app.api.controllers.neighbourhood.is_property_admin",
        new=AsyncMock(return_value=True),
    ), patch(
        "app.api.controllers.neighbourhood.create_neighbourhood_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await create_neighbourhood(payload, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        name=payload.name,
        location=payload.location,
        property_id=payload.property_id,
        db=DB,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_properties_delegates_to_service():
    expected = [make_property()]

    with patch(
        "app.api.controllers.neighbourhood.get_neighbourhood_properties_service",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_neighbourhood_properties(DB, CLAIMS)

    assert response is expected
    handler.assert_awaited_once_with(
        db=DB,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_properties_propagates_service_error():
    error = HTTPException(
        status_code=404,
        detail="No properties found for the user",
    )

    with patch(
        "app.api.controllers.neighbourhood.get_neighbourhood_properties_service",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_neighbourhood_properties(DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        db=DB,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_members_delegates_to_service():
    expected = [make_member()]

    with patch(
        "app.api.controllers.neighbourhood.get_neighbourhood_members_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_neighbourhood_members(
            NEIGHBOURHOOD_ID,
            DB,
            CLAIMS,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        db=DB,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_members_propagates_service_error():
    error = HTTPException(
        status_code=403,
        detail="Only neighbourhood admins can view members",
    )

    with patch(
        "app.api.controllers.neighbourhood.get_neighbourhood_members_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_neighbourhood_members(
                NEIGHBOURHOOD_ID,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        db=DB,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_update_neighbourhood_member_role_delegates_and_wraps_response():
    payload = UpdateMemberRoleReq(
        role=NeighbourhoodRole.SECURITY_OFFICER,
    )
    updated_member = make_member()
    updated_member.role = NeighbourhoodRole.SECURITY_OFFICER

    with patch(
        "app.api.controllers.neighbourhood.update_neighbourhood_member_role_handler",
        new=AsyncMock(return_value=updated_member),
    ) as handler:
        response = await update_neighbourhood_member_role(
            NEIGHBOURHOOD_ID,
            MEMBER_USER_ID,
            payload,
            DB,
            CLAIMS,
        )

    assert isinstance(response, UpdateMemberRoleRes)
    assert response.status == 200
    assert response.message == (
        "Neighbourhood member role updated successfully"
    )
    assert response.data == updated_member

    handler.assert_awaited_once_with(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        member_user_id=MEMBER_USER_ID,
        new_role=payload.role,
        db=DB,
        claims=CLAIMS,
    )


@pytest.mark.asyncio
async def test_update_neighbourhood_member_role_propagates_service_error():
    payload = UpdateMemberRoleReq(
        role=NeighbourhoodRole.SECURITY_OFFICER,
    )
    error = HTTPException(
        status_code=409,
        detail="The role change would leave the neighbourhood without an admin",
    )

    with patch(
        "app.api.controllers.neighbourhood.update_neighbourhood_member_role_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await update_neighbourhood_member_role(
                NEIGHBOURHOOD_ID,
                MEMBER_USER_ID,
                payload,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        member_user_id=MEMBER_USER_ID,
        new_role=payload.role,
        db=DB,
        claims=CLAIMS,
    )