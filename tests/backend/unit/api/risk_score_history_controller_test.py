from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.controllers.risk_score_history import (
    get_neighbourhood_score,
    get_neighbourhood_score_history,
)
from app.models.risk_score_history import RiskLevel
from app.schemas.risk_score_history import (
    NeighbourhoodRiskScoreHistoryRes,
    NeighbourhoodRiskScoreRes,
    RiskScoreRes,
)


NEIGHBOURHOOD_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()
CALCULATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_risk_score():
    return RiskScoreRes(
        neighbourhood_id=NEIGHBOURHOOD_ID,
        score=75.5,
        classification=RiskLevel.HIGH,
        alert_count=12,
        calculated_at=CALCULATED_AT,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_score_delegates_and_wraps_response():
    expected_score = make_risk_score()

    with patch(
        "app.api.controllers.risk_score_history.get_neighbourhood_score_handler",
        new=AsyncMock(return_value=expected_score),
    ) as handler:
        response = await get_neighbourhood_score(
            NEIGHBOURHOOD_ID,
            DB,
            CLAIMS,
        )

    assert isinstance(response, NeighbourhoodRiskScoreRes)
    assert response.status == 200
    assert response.message == "Risk Score retrieved successfully"
    assert response.data == expected_score

    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_score_propagates_service_error():
    error = HTTPException(
        status_code=403,
        detail="Not authorised for this neighbourhood",
    )

    with patch(
        "app.api.controllers.risk_score_history.get_neighbourhood_score_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_neighbourhood_score(
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
async def test_get_neighbourhood_score_history_delegates_and_wraps_response():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, tzinfo=timezone.utc)
    expected_history = [
        make_risk_score(),
        RiskScoreRes(
            neighbourhood_id=NEIGHBOURHOOD_ID,
            score=25.0,
            classification=RiskLevel.LOW,
            alert_count=3,
            calculated_at=CALCULATED_AT,
        ),
    ]

    with patch(
        "app.api.controllers.risk_score_history.get_neighbourhood_score_history_handler",
        new=AsyncMock(return_value=expected_history),
    ) as handler:
        response = await get_neighbourhood_score_history(
            NEIGHBOURHOOD_ID,
            "day",
            DB,
            CLAIMS,
            start,
            end,
        )

    assert isinstance(response, NeighbourhoodRiskScoreHistoryRes)
    assert response.status == 200
    assert response.message == "Risk Score history retrieved successfully"
    assert response.data == expected_history

    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        "day",
        DB,
        CLAIMS,
        start,
        end,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_score_history_uses_optional_date_filters():
    expected_history = [make_risk_score()]

    with patch(
        "app.api.controllers.risk_score_history.get_neighbourhood_score_history_handler",
        new=AsyncMock(return_value=expected_history),
    ) as handler:
        response = await get_neighbourhood_score_history(
            NEIGHBOURHOOD_ID,
            "week",
            DB,
            CLAIMS,
        )

    assert response.status == 200
    assert response.data == expected_history

    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        "week",
        DB,
        CLAIMS,
        None,
        None,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_score_history_propagates_service_error():
    error = HTTPException(
        status_code=400,
        detail="Invalid granularity",
    )

    with patch(
        "app.api.controllers.risk_score_history.get_neighbourhood_score_history_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_neighbourhood_score_history(
                NEIGHBOURHOOD_ID,
                "invalid",
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        "invalid",
        DB,
        CLAIMS,
        None,
        None,
    )