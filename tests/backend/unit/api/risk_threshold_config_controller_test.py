from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.controllers.risk_threshold_config import (
    get_neighbourhood_risk_threshold,
    update_neighbourhood_risk_threshold,
)
from app.schemas.risk_threshold_config import (
    NeighbourhoodRiskThresholdConfigRes,
    RiskThresholdConfigRes,
    UpdateRiskThresholdConfigReq,
)


NEIGHBOURHOOD_ID = uuid4()
CLAIMS = {
    "id": "11111111-1111-1111-1111-111111111111",
    "sub": "cognito-sub-123",
}
DB = Mock()
CONFIG_ID = uuid4()
UPDATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_threshold_config():
    return RiskThresholdConfigRes(
        id=CONFIG_ID,
        neighbourhood_id=NEIGHBOURHOOD_ID,
        low_max=30.0,
        medium_max=70.0,
        updated_at=UPDATED_AT,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_risk_threshold_delegates_and_wraps_response():
    expected_config = make_threshold_config()

    with patch(
        "app.api.controllers.risk_threshold_config.get_neighbourhood_risk_threshold_handler",
        new=AsyncMock(return_value=expected_config),
    ) as handler:
        response = await get_neighbourhood_risk_threshold(
            NEIGHBOURHOOD_ID,
            DB,
            CLAIMS,
        )

    assert isinstance(response, NeighbourhoodRiskThresholdConfigRes)
    assert response.status == 200
    assert response.message == (
        "Neighbourhood risk threshold retrieved successfully"
    )
    assert response.data == expected_config

    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_get_neighbourhood_risk_threshold_propagates_service_error():
    error = HTTPException(
        status_code=403,
        detail="Not authorised for this neighbourhood",
    )

    with patch(
        "app.api.controllers.risk_threshold_config.get_neighbourhood_risk_threshold_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await get_neighbourhood_risk_threshold(
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
async def test_update_neighbourhood_risk_threshold_delegates_and_wraps_response():
    payload = UpdateRiskThresholdConfigReq(
        low_max=35.0,
        medium_max=75.0,
    )
    expected_config = make_threshold_config()
    expected_config.low_max = 35.0
    expected_config.medium_max = 75.0

    with patch(
        "app.api.controllers.risk_threshold_config.update_neighbourhood_risk_threshold_handler",
        new=AsyncMock(return_value=expected_config),
    ) as handler:
        response = await update_neighbourhood_risk_threshold(
            NEIGHBOURHOOD_ID,
            payload,
            DB,
            CLAIMS,
        )

    assert isinstance(response, NeighbourhoodRiskThresholdConfigRes)
    assert response.status == 200
    assert response.message == (
        "Neighbourhood risk threshold retrieved successfully"
    )
    assert response.data == expected_config

    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        payload,
        DB,
        CLAIMS,
    )


@pytest.mark.asyncio
async def test_update_neighbourhood_risk_threshold_propagates_service_error():
    payload = UpdateRiskThresholdConfigReq(
        low_max=35.0,
    )
    error = HTTPException(
        status_code=403,
        detail="Not authorised for this neighbourhood",
    )

    with patch(
        "app.api.controllers.risk_threshold_config.update_neighbourhood_risk_threshold_handler",
        new=AsyncMock(side_effect=error),
    ) as handler:
        with pytest.raises(HTTPException) as exc_info:
            await update_neighbourhood_risk_threshold(
                NEIGHBOURHOOD_ID,
                payload,
                DB,
                CLAIMS,
            )

    assert exc_info.value is error
    handler.assert_awaited_once_with(
        NEIGHBOURHOOD_ID,
        payload,
        DB,
        CLAIMS,
    )


def test_update_risk_threshold_config_requires_at_least_one_value():
    with pytest.raises(ValidationError):
        UpdateRiskThresholdConfigReq(
            low_max=None,
            medium_max=None,
        )


def test_update_risk_threshold_config_accepts_only_low_max():
    payload = UpdateRiskThresholdConfigReq(
        low_max=35.0,
    )

    assert payload.low_max == 35.0
    assert payload.medium_max is None


def test_update_risk_threshold_config_accepts_only_medium_max():
    payload = UpdateRiskThresholdConfigReq(
        medium_max=75.0,
    )

    assert payload.low_max is None
    assert payload.medium_max == 75.0