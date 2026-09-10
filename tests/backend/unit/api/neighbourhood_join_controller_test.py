from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.controllers.neighbourhood_join import (
    get_join_code,
    join_neighbourhood,
    list_join_requests,
    regenerate_join_code,
    resolve_join_request,
)
from app.schemas.neighbourhood_join import (
    JoinCodeRes,
    JoinNeighbourhoodReq,
    JoinNeighbourhoodRes,
    JoinRequestRes,
    RegenerateJoinCodeRes,
    ResolveJoinRequestReq,
    ResolveJoinRequestRes,
)


PROPERTY_ID = uuid4()
NEIGHBOURHOOD_ID = uuid4()
REQUEST_ID = uuid4()
USER_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_join_request():
    return JoinRequestRes(
        id=REQUEST_ID,
        neighbourhood_id=NEIGHBOURHOOD_ID,
        property_id=PROPERTY_ID,
        user_id=USER_ID,
        status="PENDING",
        created_at=CREATED_AT,
    )


@pytest.mark.asyncio
async def test_join_neighbourhood_delegates_and_wraps_response():
    payload = JoinNeighbourhoodReq(join_code="ABC123")
    expected_request = make_join_request()

    with patch(
        "app.api.controllers.neighbourhood_join.request_to_join_handler",
        new=AsyncMock(return_value=expected_request),
    ) as handler:
        response = await join_neighbourhood(
            PROPERTY_ID,
            payload,
            DB,
            CLAIMS,
        )

    assert isinstance(response, JoinNeighbourhoodRes)
    assert response.status == 201
    assert response.message == "Join request submitted"
    assert response.data == expected_request

    handler.assert_awaited_once_with(
        PROPERTY_ID,
        payload.join_code,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_join_neighbourhood_propagates_service_error():
    payload = JoinNeighbourhoodReq(join_code="INVALID")
    error = HTTPException(
        status_code=404,
        detail="Invalid join code",
    )

    with patch(
        "app.api.controllers.neighbourhood_join.request_to_join_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await join_neighbourhood(
                PROPERTY_ID,
                payload,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        PROPERTY_ID,
        payload.join_code,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_list_join_requests_delegates_to_service():
    expected = [make_join_request()]

    with patch(
        "app.api.controllers.neighbourhood_join.list_join_requests_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await list_join_requests(
            NEIGHBOURHOOD_ID,
            DB,
            CLAIMS,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_list_join_requests_propagates_service_error():
    error = HTTPException(
        status_code=403,
        detail="Insufficient permissions",
    )

    with patch(
        "app.api.controllers.neighbourhood_join.list_join_requests_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await list_join_requests(
                NEIGHBOURHOOD_ID,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_resolve_join_request_delegates_and_wraps_response():
    payload = ResolveJoinRequestReq(action="approve")
    expected_request = make_join_request()
    expected_request.status = "APPROVED"

    with patch(
        "app.api.controllers.neighbourhood_join.resolve_join_request_handler",
        new=AsyncMock(return_value=expected_request),
    ) as handler:
        response = await resolve_join_request(
            REQUEST_ID,
            payload,
            DB,
            CLAIMS,
        )

    assert isinstance(response, ResolveJoinRequestRes)
    assert response.status == 200
    assert response.message == "Join request updated"
    assert response.data == expected_request

    handler.assert_awaited_once_with(
        REQUEST_ID,
        payload.action,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_resolve_join_request_propagates_service_error():
    payload = ResolveJoinRequestReq(action="DENY")
    error = HTTPException(
        status_code=409,
        detail="Join request has already been resolved",
    )

    with patch(
        "app.api.controllers.neighbourhood_join.resolve_join_request_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await resolve_join_request(
                REQUEST_ID,
                payload,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        REQUEST_ID,
        payload.action,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_regenerate_join_code_delegates_to_service():
    expected = RegenerateJoinCodeRes(join_code="NEWCODE123")

    with patch(
        "app.api.controllers.neighbourhood_join.regenerate_join_code_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await regenerate_join_code(
            NEIGHBOURHOOD_ID,
            DB,
            CLAIMS,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_regenerate_join_code_propagates_service_error():
    error = HTTPException(
        status_code=403,
        detail="Insufficient permissions",
    )

    with patch(
        "app.api.controllers.neighbourhood_join.regenerate_join_code_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await regenerate_join_code(
                NEIGHBOURHOOD_ID,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_join_code_delegates_to_service():
    expected = JoinCodeRes(join_code="ABC123")

    with patch(
        "app.api.controllers.neighbourhood_join.get_join_code_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        response = await get_join_code(
            NEIGHBOURHOOD_ID,
            DB,
            CLAIMS,
        )

    assert response is expected
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_join_code_propagates_service_error():
    error = HTTPException(
        status_code=404,
        detail="Neighbourhood not found",
    )

    with patch(
        "app.api.controllers.neighbourhood_join.get_join_code_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_join_code(
                NEIGHBOURHOOD_ID,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


def test_join_neighbourhood_request_requires_join_code():
    with pytest.raises(ValidationError):
        JoinNeighbourhoodReq()


def test_resolve_join_request_requires_valid_action():
    with pytest.raises(ValidationError):
        ResolveJoinRequestReq(action="INVALID")


def test_resolve_join_request_normalizes_action_to_uppercase():
    payload = ResolveJoinRequestReq(action="approve")

    assert payload.action == "APPROVE"