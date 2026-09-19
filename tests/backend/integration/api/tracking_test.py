from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

import main as app_main
from app.auth.dependencies import get_authenticated_edge_agent
from app.core.database import get_db
from app.schemas.tracking import (
    TrackingMatchData,
    TrackingMatchResponse,
    TrackingSightingCreateData,
    TrackingSightingCreateResponse,
    TrackingTimelineData,
    TrackingTimelineResponse,
)


CAMERA_ID = uuid4()
PROPERTY_ID = uuid4()
ALERT_ID = uuid4()
SUBJECT_ID = uuid4()
SIGHTING_ID = uuid4()


async def override_edge_agent():
    return SimpleNamespace(property_id=PROPERTY_ID)


async def override_db():
    # These route tests mock the service layer, so no database connection
    # is required for this simulated API test.
    yield object()


@pytest.fixture
def simulated_tracking_dependencies():
    app_main.app.dependency_overrides[get_authenticated_edge_agent] = (
        override_edge_agent
    )
    app_main.app.dependency_overrides[get_db] = override_db

    yield

    app_main.app.dependency_overrides.pop(
        get_authenticated_edge_agent,
        None,
    )
    app_main.app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_tracking_match_endpoint_returns_existing_subject(
    async_client,
    simulated_tracking_dependencies,
):
    expected_response = TrackingMatchResponse(
        status=200,
        message="Tracking subject matched",
        data=TrackingMatchData(
            matched=True,
            tracking_subject_id=SUBJECT_ID,
            similarity=0.91,
            threshold=0.75,
        ),
    )

    with patch(
        "app.api.controllers.internal.match_tracking_embedding",
        new=AsyncMock(return_value=expected_response),
    ) as match_handler:
        response = await async_client.post(
            "/internal/tracking/match",
            headers={"X-Internal-Token": "simulated-token"},
            json={
                "camera_id": str(CAMERA_ID),
                "appearance_embedding": [1.0] + [0.0] * 1279,
                "embedding_model": (
                    "deep_sort_mobilenet_v2_bottleneck"
                ),
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["matched"] is True
    assert response.json()["data"]["tracking_subject_id"] == str(SUBJECT_ID)

    match_handler.assert_awaited_once()
    assert match_handler.await_args.kwargs["candidate_property_id"] == PROPERTY_ID


@pytest.mark.asyncio
async def test_tracking_sighting_endpoint_returns_parent_alert(
    async_client,
    simulated_tracking_dependencies,
):
    expected_response = TrackingSightingCreateResponse(
        status=201,
        message="Tracking sighting recorded and broadcast",
        data=TrackingSightingCreateData(
            alert_id=ALERT_ID,
            tracking_subject_id=SUBJECT_ID,
            sighting_id=SIGHTING_ID,
            camera_id=CAMERA_ID,
            sequence_no=2,
            match_confidence=0.91,
        ),
    )

    with patch(
        "app.api.controllers.internal.record_tracking_sighting_for_agent",
        new=AsyncMock(return_value=expected_response),
    ) as sighting_handler:
        response = await async_client.post(
            "/internal/tracking/sightings",
            headers={"X-Internal-Token": "simulated-token"},
            json={
                "tracking_subject_id": str(SUBJECT_ID),
                "camera_id": str(CAMERA_ID),
                "local_track_id": 17,
                "observed_at": "2026-09-18T10:00:00+00:00",
                "match_confidence": 0.91,
            },
        )

    assert response.status_code == 201
    assert response.json()["data"]["alert_id"] == str(ALERT_ID)
    assert response.json()["data"]["sequence_no"] == 2

    sighting_handler.assert_awaited_once()
    assert sighting_handler.await_args.kwargs["candidate_property_id"] == PROPERTY_ID


@pytest.mark.asyncio
async def test_tracking_timeline_endpoint_returns_ordered_sightings(
    async_client,
    simulated_tracking_dependencies,
):
    expected_response = TrackingTimelineResponse(
        status=200,
        message="Tracking timeline retrieved",
        data=TrackingTimelineData(
            alert_id=ALERT_ID,
            tracking_subject_id=SUBJECT_ID,
            alert_status="OPEN",
            sightings=[
                {
                    "id": SIGHTING_ID,
                    "camera_id": CAMERA_ID,
                    "camera_name": "Front Gate",
                    "camera_location": "North entrance",
                    "local_track_id": 17,
                    "observed_at": "2026-09-18T10:00:00+00:00",
                    "sequence_no": 2,
                    "match_confidence": 0.91,
                }
            ],
        ),
    )

    with patch(
        "app.api.controllers.alert.get_tracking_timeline",
        new=AsyncMock(return_value=expected_response),
    ) as timeline_handler:
        response = await async_client.get(
            f"/alerts/{ALERT_ID}/tracking",
            headers={
                "Authorization": "Bearer test",
                "X-Mock-Role": "SECURITY_OFFICER",
                "X-Mock-Sub": str(uuid4()),
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["tracking_subject_id"] == str(SUBJECT_ID)
    assert response.json()["data"]["sightings"][0]["sequence_no"] == 2

    timeline_handler.assert_awaited_once()