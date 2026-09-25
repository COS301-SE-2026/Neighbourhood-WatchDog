from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.dispatch import get_alert_dispatch, router, respond_to_dispatch
from app.models.dispatch import DispatchStatus
from app.models.security_officer import AvailabilityStatus
from app.schemas.dispatch import AlertDispatchRes, DispatchCandidateRes, RespondDispatchReq, RespondDispatchRes

ALERT_ID = uuid4()
OFFICER_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)

def make_dispatch_res():
    selected = DispatchCandidateRes(
        id=uuid4(),
        alert_id=ALERT_ID,
        officer_id=OFFICER_ID,
        rank=1,
        score=2.5,
        distance=800.0,
        eta=120.0,
        workload=0,
        status=DispatchStatus.SELECTED,
        officer_availability=AvailabilityStatus.AVAILABLE,
        is_location_stale=False,
        created_at=CREATED_AT,
        notified_at=None,
        responded_at=None,
    )
    return AlertDispatchRes(alert_id=ALERT_ID, selected=selected)

def test_router_exposes_get_dispatch_route():
    routes = {(route.path, tuple(sorted(route.methods))) for route in router.routes}
    assert ("/dispatch/alert/{alert_id}", ("GET",)) in routes

@pytest.mark.asyncio
async def test_get_alert_dispatch_delegates_to_service():
    expected = make_dispatch_res()

    with patch(
        "app.api.controllers.dispatch.get_alert_dispatch_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        res = await get_alert_dispatch(ALERT_ID, DB, CLAIMS)

    assert res is expected
    handler.assert_awaited_once_with(
        alert_id=ALERT_ID,
        db=DB,
        claims=CLAIMS,
    )

@pytest.mark.asyncio
async def test_get_alert_dispatch_unchanged_when_returns_empty():
    expected = AlertDispatchRes(alert_id=ALERT_ID, no_candidate=True)

    with patch(
        "app.api.controllers.dispatch.get_alert_dispatch_handler",
        new=AsyncMock(return_value=expected),
    ):
        res = await get_alert_dispatch(ALERT_ID, DB, CLAIMS)

    assert res is expected
    assert res.no_candidate is True
    assert res.selected is None

@pytest.mark.asyncio
async def test_get_alert_dispatch_propagates_unauthenticated_error():
    error = HTTPException(status_code=401, detail="Not authenticated")

    with patch(
        "app.api.controllers.dispatch.get_alert_dispatch_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_alert_dispatch(ALERT_ID, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        alert_id=ALERT_ID,
        db=DB,
        claims=CLAIMS,
    )

@pytest.mark.asyncio
async def test_get_alert_dispatch_propagates_forbidden_error():
    error = HTTPException(status_code=403, detail="Not authorised to view dispatch for this alert")

    with patch(
        "app.api.controllers.dispatch.get_alert_dispatch_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_alert_dispatch(ALERT_ID, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        alert_id=ALERT_ID,
        db=DB,
        claims=CLAIMS,
    )

@pytest.mark.asyncio
async def test_get_alert_dispatch_propagates_not_found_error():
    error = HTTPException(status_code=404, detail="Alert not found")

    with patch(
        "app.api.controllers.dispatch.get_alert_dispatch_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_alert_dispatch(ALERT_ID, DB, CLAIMS)

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        alert_id=ALERT_ID,
        db=DB,
        claims=CLAIMS,
    )

def test_router_exposes_respond_dispatch_route():
    routes = {(route.path, tuple(sorted(route.methods))) for route in router.routes}
    assert ("/dispatch/{dispatch_id}/respond", ("POST",)) in routes

@pytest.mark.asyncio
async def test_respond_to_dispatch_delegates_to_service():
    dispatch_id = uuid4()
    body = RespondDispatchReq(action="ACCEPT")
    expected = RespondDispatchRes(status=200, message="Accepted", data=None)

    with patch(
        "app.api.controllers.dispatch.respond_to_dispatch_handler",
        new=AsyncMock(return_value=expected),
    ) as handler:
        res = await respond_to_dispatch(dispatch_id, body, DB, CLAIMS)

    assert res is expected
    handler.assert_awaited_once_with(
        dispatch_id=dispatch_id,
        action="ACCEPT",
        db=DB,
        claims=CLAIMS,
    )

@pytest.mark.asyncio
async def test_respond_to_dispatch_propagates_forbidden_error():
    dispatch_id = uuid4()
    body = RespondDispatchReq(action="ACCEPT")
    error = HTTPException(status_code=403, detail="This dispatch request was not sent to you")

    with patch(
        "app.api.controllers.dispatch.respond_to_dispatch_handler",
        new=AsyncMock(side_effect=error),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await respond_to_dispatch(dispatch_id, body, DB, CLAIMS)

    assert exc_info.value is error

@pytest.mark.asyncio
async def test_respond_to_dispatch_propagates_conflict_error():
    dispatch_id = uuid4()
    body = RespondDispatchReq(action="ACCEPT")
    error = HTTPException(status_code=409, detail="This alert has already been assigned to another officer")

    with patch(
        "app.api.controllers.dispatch.respond_to_dispatch_handler",
        new=AsyncMock(side_effect=error),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await respond_to_dispatch(dispatch_id, body, DB, CLAIMS)

    assert exc_info.value is error