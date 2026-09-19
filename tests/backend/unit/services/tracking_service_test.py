from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.tracking import (
    MatchTrackingEmbeddingRequest,
    RecordTrackingSightingRequest,
)
from app.services.tracking_service import (
    _require_tracking_timeline_access,
    get_tracking_timeline,
    match_tracking_embedding,
    normalize_appearance_embedding,
    record_tracking_sighting,
    record_tracking_sighting_for_agent,
)


def test_normalise_appearance_embedding_returns_unit_vector():
    result = normalize_appearance_embedding([3.0, 4.0] + [0.0] * 1278)

    assert result is not None
    assert result[0] == 0.6
    assert result[1] == 0.8
    assert len(result) == 1280

def test_normalise_appearance_embedding_rejects_wrong_dimension():
    with pytest.raises(HTTPException) as exc:
        normalize_appearance_embedding([1.0, 2.0])

    assert exc.value.status_code == 422

def test_normalise_appearance_embedding_rejects_zero_vector():
    with pytest.raises(HTTPException) as exc:
        normalize_appearance_embedding([0.0] * 1280)

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_http_exception_is_reraised():
    """
    Covers:

        except HTTPException:
            raise

    The original HTTPException should pass through unchanged.
    """

    db = MagicMock()
    tracking_subject_id = uuid4()
    camera_id = uuid4()
    observed_at = datetime.now(timezone.utc)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=tracking_subject_id,
            camera_id=camera_id,
            local_track_id=1,
            observed_at=observed_at,
            match_confidence=1.5,
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "match confidence must be between 0 and 1"


@pytest.mark.asyncio
async def test_integrity_error_is_converted_to_409():
    """
    Covers:

        except IntegrityError as exc:
            await db.rollback()
            logger.warning(...)
            raise HTTPException(status_code=409, ...)

    Forces the database execute operation to raise IntegrityError.
    """

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=IntegrityError(
            "duplicate",
            {},
            Exception("duplicate constraint"),
        )
    )
    db.rollback = AsyncMock()
    tracking_subject_id = uuid4()
    camera_id = uuid4()
    observed_at = datetime.now(timezone.utc)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=tracking_subject_id,
            camera_id=camera_id,
            local_track_id=1,
            observed_at=observed_at,
        )

    assert exc.value.status_code == 409
    assert (
        exc.value.detail
        == "Tracking sighting could not be recorded"
    )

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_unexpected_exception_is_converted_to_500():
    """
    Covers:

        except Exception as exc:
            await db.rollback()
            logger.exception(...)
            raise HTTPException(status_code=500, ...)

    Forces an unexpected database error.
    """

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=RuntimeError("database connection failed")
    )
    db.rollback = AsyncMock()
    tracking_subject_id = uuid4()
    camera_id = uuid4()
    observed_at = datetime.now(timezone.utc)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=tracking_subject_id,
            camera_id=camera_id,
            local_track_id=1,
            observed_at=observed_at,
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Failed to record tracking sighting"

    db.rollback.assert_awaited_once()


@pytest.mark.parametrize(
    ("values", "detail"),
    [
        ([float("nan")] + [0.0] * 1279, "appearance_embedding must contain only finite values"),
        (["not-a-number"] + [0.0] * 1279, "appearance_embedding must contain numeric values"),
    ],
)
def test_normalise_appearance_embedding_rejects_invalid_values(values, detail):
    with pytest.raises(HTTPException) as exc:
        normalize_appearance_embedding(values)

    assert exc.value.status_code == 422
    assert exc.value.detail == detail


def test_normalise_appearance_embedding_accepts_none():
    assert normalize_appearance_embedding(None) is None


@pytest.mark.asyncio
async def test_record_tracking_sighting_creates_next_sequence():
    subject = SimpleNamespace(id=uuid4())
    alert = SimpleNamespace(status="OPEN")
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (subject, alert)
    duplicate_result = MagicMock()
    duplicate_result.scalar_one_or_none.return_value = None
    sequence_result = MagicMock()
    sequence_result.scalar_one.return_value = 4

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[subject_result, duplicate_result, sequence_result])
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    sighting = await record_tracking_sighting(
        db=db,
        tracking_subject_id=subject.id,
        camera_id=uuid4(),
        local_track_id=7,
        observed_at=datetime.now(timezone.utc),
        match_confidence=0.8,
    )

    assert sighting.sequence_no == 4
    assert sighting.local_track_id == 7
    db.add.assert_called_once_with(sighting)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(sighting)


@pytest.mark.asyncio
async def test_record_tracking_sighting_rejects_terminated_alert():
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(status="ACKNOWLEDGED"),
    )
    db = MagicMock()
    db.execute = AsyncMock(return_value=subject_result)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=uuid4(),
            camera_id=uuid4(),
            local_track_id=1,
            observed_at=datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "Tracking sequence has already terminated"


@pytest.mark.asyncio
async def test_record_tracking_sighting_rejects_duplicate_camera():
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(status="OPEN"),
    )
    duplicate_result = MagicMock()
    duplicate_result.scalar_one_or_none.return_value = uuid4()
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[subject_result, duplicate_result])

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=uuid4(),
            camera_id=uuid4(),
            local_track_id=1,
            observed_at=datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "Tracking subject already has a sighting on this camera"


@pytest.mark.asyncio
async def test_record_tracking_sighting_rejects_missing_subject():
    result = MagicMock()
    result.one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=db,
            tracking_subject_id=uuid4(),
            camera_id=uuid4(),
            local_track_id=1,
            observed_at=datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Tracking subject and related Alert not found"


@pytest.mark.asyncio
async def test_record_tracking_sighting_rejects_negative_local_track_id():
    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting(
            db=MagicMock(),
            tracking_subject_id=uuid4(),
            camera_id=uuid4(),
            local_track_id=-1,
            observed_at=datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "local track id cannot be negative"


def make_agent_sighting_body():
    return RecordTrackingSightingRequest(
        tracking_subject_id=uuid4(),
        camera_id=uuid4(),
        local_track_id=17,
        observed_at=datetime.now(timezone.utc),
        match_confidence=0.91,
    )


@pytest.mark.asyncio
async def test_agent_sighting_rejects_unknown_camera():
    result = MagicMock()
    result.one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting_for_agent(
            db=db,
            body=make_agent_sighting_body(),
            candidate_property_id=uuid4(),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Candidate camera not found"


@pytest.mark.asyncio
async def test_agent_sighting_rejects_camera_outside_candidate_property():
    body = make_agent_sighting_body()
    candidate_camera = SimpleNamespace(property_id=uuid4())
    candidate_property = SimpleNamespace(neighbourhood_id=uuid4())
    result = MagicMock()
    result.one_or_none.return_value = (candidate_camera, candidate_property)
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting_for_agent(
            db=db,
            body=body,
            candidate_property_id=uuid4(),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "The edge agent is not authorized for this camera"


@pytest.mark.asyncio
async def test_agent_sighting_rejects_camera_without_neighbourhood():
    body = make_agent_sighting_body()
    property_id = uuid4()
    candidate_camera = SimpleNamespace(property_id=property_id)
    candidate_property = SimpleNamespace(neighbourhood_id=None)
    result = MagicMock()
    result.one_or_none.return_value = (candidate_camera, candidate_property)
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting_for_agent(
            db=db,
            body=body,
            candidate_property_id=property_id,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Candidate camera is not associated with a neighbourhood"


@pytest.mark.asyncio
async def test_agent_sighting_rejects_unknown_tracking_subject():
    body = make_agent_sighting_body()
    property_id = uuid4()
    candidate_result = MagicMock()
    candidate_result.one_or_none.return_value = (
        SimpleNamespace(property_id=property_id),
        SimpleNamespace(neighbourhood_id=uuid4()),
    )
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[candidate_result, subject_result])

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting_for_agent(
            db=db,
            body=body,
            candidate_property_id=property_id,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Tracking subject not found"


@pytest.mark.asyncio
async def test_agent_sighting_rejects_subject_from_other_neighbourhood():
    body = make_agent_sighting_body()
    property_id = uuid4()
    candidate_neighbourhood = uuid4()
    candidate_result = MagicMock()
    candidate_result.one_or_none.return_value = (
        SimpleNamespace(property_id=property_id),
        SimpleNamespace(neighbourhood_id=candidate_neighbourhood),
    )
    source_result = MagicMock()
    source_result.one_or_none.return_value = (
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(),
        SimpleNamespace(neighbourhood_id=uuid4()),
    )
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[candidate_result, source_result])

    with pytest.raises(HTTPException) as exc:
        await record_tracking_sighting_for_agent(
            db=db,
            body=body,
            candidate_property_id=property_id,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Tracking subject belongs to a different neighbourhood"


@pytest.mark.asyncio
async def test_agent_sighting_records_and_broadcasts_event():
    body = make_agent_sighting_body()
    property_id = uuid4()
    neighbourhood_id = uuid4()
    subject_id = body.tracking_subject_id
    alert_id = uuid4()
    sighting = SimpleNamespace(id=uuid4(), sequence_no=2)
    candidate_result = MagicMock()
    candidate_result.one_or_none.return_value = (
        SimpleNamespace(
            property_id=property_id,
            name="Back Gate",
            location="Northern boundary"

        ),
        SimpleNamespace(neighbourhood_id=neighbourhood_id),
    )
    source_result = MagicMock()
    source_result.one_or_none.return_value = (
        SimpleNamespace(id=subject_id),
        SimpleNamespace(id=alert_id),
        SimpleNamespace(),
        SimpleNamespace(neighbourhood_id=neighbourhood_id),
    )
    recipient_result = MagicMock()
    recipient_result.scalars.return_value.all.return_value = [uuid4()]
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[candidate_result, source_result, recipient_result])

    with (
        patch(
            "app.services.tracking_service.record_tracking_sighting",
            new=AsyncMock(return_value=sighting),
        ) as record_sighting,
        patch(
            "app.api.controllers.alert.broadcast",
            new=AsyncMock(),
        ) as broadcast,
    ):
        response = await record_tracking_sighting_for_agent(
            db=db,
            body=body,
            candidate_property_id=property_id,
        )

    assert response.status == 201
    assert response.data.sighting_id == sighting.id
    record_sighting.assert_awaited_once()
    broadcast.assert_awaited_once()
    assert broadcast.call_args.args[0] == [str(recipient_result.scalars.return_value.all.return_value[0])]

    broadcast_message = broadcast.call_args.args[1]

    assert broadcast_message["event"] == "tracking.sighting"

    payload = broadcast_message["payload"]

    assert payload["event_id"] == str(sighting.id)
    assert payload["event_type"] == "cross_property_match"
    assert payload["alert_id"] == str(alert_id)
    assert payload["tracking_subject_id"] == str(subject_id)
    assert payload["sighting_id"] == str(sighting.id)
    assert payload["camera_name"] == "Back Gate"
    assert payload["camera_location"] == "Northern boundary"
    assert payload["sequence_no"] == sighting.sequence_no
    assert payload["match_confidence"] == body.match_confidence


@pytest.mark.asyncio
async def test_agent_sighting_survives_broadcast_failure():
    body = make_agent_sighting_body()
    property_id = uuid4()
    neighbourhood_id = uuid4()
    candidate_result = MagicMock()
    candidate_result.one_or_none.return_value = (
        SimpleNamespace(property_id=property_id),
        SimpleNamespace(neighbourhood_id=neighbourhood_id),
    )
    source_result = MagicMock()
    source_result.one_or_none.return_value = (
        SimpleNamespace(id=body.tracking_subject_id),
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(),
        SimpleNamespace(neighbourhood_id=neighbourhood_id),
    )
    recipient_result = MagicMock()
    recipient_result.scalars.return_value.all.return_value = []
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[candidate_result, source_result, recipient_result])

    with (
        patch(
            "app.services.tracking_service.record_tracking_sighting",
            new=AsyncMock(return_value=SimpleNamespace(id=uuid4(), sequence_no=1)),
        ),
        patch(
            "app.api.controllers.alert.broadcast",
            new=AsyncMock(side_effect=RuntimeError("websocket unavailable")),
        ),
    ):
        response = await record_tracking_sighting_for_agent(
            db=db,
            body=body,
            candidate_property_id=property_id,
        )

    assert response.status == 201


@pytest.mark.asyncio
async def test_match_tracking_embedding_rejects_unsupported_model():
    body = SimpleNamespace(
        embedding_model="unsupported-model",
        appearance_embedding=[1.0] + [0.0] * 1279,
        camera_id=uuid4(),
    )

    with pytest.raises(HTTPException) as exc:
        await match_tracking_embedding(
            db=MagicMock(),
            body=body,
            candidate_property_id=uuid4(),
        )

    assert exc.value.status_code == 422
    assert "Unsupported appearance embedding model" in exc.value.detail


@pytest.mark.asyncio
async def test_match_tracking_embedding_requires_embedding():
    body = SimpleNamespace(
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
        appearance_embedding=None,
        camera_id=uuid4(),
    )

    with pytest.raises(HTTPException) as exc:
        await match_tracking_embedding(
            db=MagicMock(),
            body=body,
            candidate_property_id=uuid4(),
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "appearance_embedding is required"


@pytest.mark.asyncio
async def test_match_tracking_embedding_rejects_unknown_camera():
    camera_result = MagicMock()
    camera_result.one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(return_value=camera_result)
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    with pytest.raises(HTTPException) as exc:
        await match_tracking_embedding(
            db=db,
            body=body,
            candidate_property_id=uuid4(),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Candidate camera not found"


@pytest.mark.asyncio
async def test_match_tracking_embedding_rejects_unauthorized_camera():
    property_id = uuid4()
    result = MagicMock()
    result.one_or_none.return_value = (
        SimpleNamespace(property_id=uuid4()),
        SimpleNamespace(neighbourhood_id=uuid4()),
    )
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    with pytest.raises(HTTPException) as exc:
        await match_tracking_embedding(
            db=db,
            body=body,
            candidate_property_id=property_id,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "The edge agent is not authorized for this camera"


@pytest.mark.asyncio
async def test_match_tracking_embedding_rejects_camera_without_neighbourhood():
    property_id = uuid4()
    result = MagicMock()
    result.one_or_none.return_value = (
        SimpleNamespace(property_id=property_id),
        SimpleNamespace(neighbourhood_id=None),
    )
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    with pytest.raises(HTTPException) as exc:
        await match_tracking_embedding(
            db=db,
            body=body,
            candidate_property_id=property_id,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Candidate camera is not associated with a neighbourhood"


@pytest.mark.asyncio
async def test_match_tracking_embedding_clamps_similarity():
    property_id = uuid4()
    camera_result = MagicMock()
    camera_result.one_or_none.return_value = (
        SimpleNamespace(property_id=property_id),
        SimpleNamespace(neighbourhood_id=uuid4()),
    )
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (SimpleNamespace(id=uuid4()), -0.5)
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[camera_result, subject_result])
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    response = await match_tracking_embedding(
        db=db,
        body=body,
        candidate_property_id=property_id,
    )

    assert response.data.matched is True
    assert response.data.similarity == 1.0


@pytest.mark.asyncio
async def test_match_tracking_embedding_clamps_negative_similarity():
    property_id = uuid4()
    camera_result = MagicMock()
    camera_result.one_or_none.return_value = (
        SimpleNamespace(property_id=property_id),
        SimpleNamespace(neighbourhood_id=uuid4()),
    )
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (SimpleNamespace(id=uuid4()), 2.0)
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[camera_result, subject_result])
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    response = await match_tracking_embedding(
        db=db,
        body=body,
        candidate_property_id=property_id,
    )

    assert response.data.matched is False
    assert response.data.similarity == 0.0


@pytest.mark.asyncio
async def test_match_tracking_embedding_accepts_exact_threshold():
    property_id = uuid4()
    camera_result = MagicMock()
    camera_result.one_or_none.return_value = (
        SimpleNamespace(property_id=property_id),
        SimpleNamespace(neighbourhood_id=uuid4()),
    )
    subject = SimpleNamespace(id=uuid4())
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (subject, 0.25)
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[camera_result, subject_result])
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    response = await match_tracking_embedding(
        db=db,
        body=body,
        candidate_property_id=property_id,
    )

    assert response.data.matched is True
    assert response.data.similarity == 0.75


@pytest.mark.asyncio
async def test_match_tracking_embedding_returns_no_match():
    property_id = uuid4()
    camera = SimpleNamespace(property_id=property_id)
    candidate_property = SimpleNamespace(neighbourhood_id=uuid4())
    camera_result = MagicMock()
    camera_result.one_or_none.return_value = (camera, candidate_property)
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[camera_result, subject_result])
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    response = await match_tracking_embedding(
        db=db,
        body=body,
        candidate_property_id=property_id,
    )

    assert response.data.matched is False
    assert response.data.tracking_subject_id is None


@pytest.mark.asyncio
async def test_match_tracking_embedding_returns_threshold_miss():
    property_id = uuid4()
    camera = SimpleNamespace(property_id=property_id)
    candidate_property = SimpleNamespace(neighbourhood_id=uuid4())
    subject = SimpleNamespace(id=uuid4())
    camera_result = MagicMock()
    camera_result.one_or_none.return_value = (camera, candidate_property)
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (subject, 1.0)
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[camera_result, subject_result])
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    response = await match_tracking_embedding(
        db=db,
        body=body,
        candidate_property_id=property_id,
    )

    assert response.data.matched is False
    assert response.data.similarity == 0.0


@pytest.mark.asyncio
async def test_match_tracking_embedding_returns_match():
    property_id = uuid4()
    camera = SimpleNamespace(property_id=property_id)
    candidate_property = SimpleNamespace(neighbourhood_id=uuid4())
    subject = SimpleNamespace(id=uuid4())
    camera_result = MagicMock()
    camera_result.one_or_none.return_value = (camera, candidate_property)
    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (subject, 0.1)
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[camera_result, subject_result])
    body = MatchTrackingEmbeddingRequest(
        camera_id=uuid4(),
        appearance_embedding=[1.0] + [0.0] * 1279,
        embedding_model="deep_sort_mobilenet_v2_bottleneck",
    )

    response = await match_tracking_embedding(
        db=db,
        body=body,
        candidate_property_id=property_id,
    )

    assert response.data.matched is True
    assert response.data.tracking_subject_id == subject.id


@pytest.mark.asyncio
async def test_tracking_timeline_access_allows_system_admin():
    db = MagicMock()

    await _require_tracking_timeline_access(
        db=db,
        claims={"custom:role": "SYSTEM_ADMIN"},
        neighbourhood_id=uuid4(),
    )

    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_tracking_timeline_access_allows_authorized_officer():
    result = MagicMock()
    result.scalar_one_or_none.return_value = SimpleNamespace(role="SECURITY_OFFICER")
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    await _require_tracking_timeline_access(
        db=db,
        claims={"id": str(uuid4())},
        neighbourhood_id=uuid4(),
    )

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_tracking_timeline_rejects_missing_alert():
    result = MagicMock()
    result.one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await get_tracking_timeline(
            db=db,
            alert_id=uuid4(),
            claims={"custom:role": "SYSTEM_ADMIN"},
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Alert not found"


@pytest.mark.asyncio
async def test_get_tracking_timeline_rejects_alert_without_neighbourhood():
    result = MagicMock()
    result.one_or_none.return_value = (
        SimpleNamespace(status="OPEN"),
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(neighbourhood_id=None),
    )
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await get_tracking_timeline(
            db=db,
            alert_id=uuid4(),
            claims={"custom:role": "SYSTEM_ADMIN"},
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Alert is not associated with a neighbourhood"


@pytest.mark.asyncio
async def test_get_tracking_timeline_rejects_missing_tracking_subject():
    alert_result = MagicMock()
    alert_result.one_or_none.return_value = (
        SimpleNamespace(status="OPEN"),
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(neighbourhood_id=uuid4()),
    )
    subject_result = MagicMock()
    subject_result.scalar_one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[alert_result, subject_result])

    with patch(
        "app.services.tracking_service._require_tracking_timeline_access",
        new=AsyncMock(),
    ):
        with pytest.raises(HTTPException) as exc:
            await get_tracking_timeline(
                db=db,
                alert_id=uuid4(),
                claims={"id": str(uuid4())},
            )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Tracking timeline not found"


@pytest.mark.asyncio
async def test_tracking_timeline_access_rejects_invalid_claims():
    with pytest.raises(HTTPException) as exc:
        await _require_tracking_timeline_access(
            db=MagicMock(),
            claims={},
            neighbourhood_id=uuid4(),
        )

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_tracking_timeline_access_rejects_unauthorized_user():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await _require_tracking_timeline_access(
            db=db,
            claims={"id": str(uuid4())},
            neighbourhood_id=uuid4(),
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_tracking_timeline_returns_ordered_data():
    alert_id = uuid4()
    subject_id = uuid4()
    alert = SimpleNamespace(status="OPEN")
    property_obj = SimpleNamespace(neighbourhood_id=uuid4())
    camera = SimpleNamespace(id=uuid4())
    subject = SimpleNamespace(id=subject_id)
    sighting = SimpleNamespace(
        id=uuid4(),
        local_track_id=9,
        observed_at=datetime.now(timezone.utc),
        sequence_no=1,
        match_confidence=0.95,
    )
    sighting_camera = SimpleNamespace(
        id=uuid4(),
        name="Front Gate",
        location="North entrance",
    )
    alert_result = MagicMock()
    alert_result.one_or_none.return_value = (alert, camera, property_obj)
    subject_result = MagicMock()
    subject_result.scalar_one_or_none.return_value = subject
    sightings_result = MagicMock()
    sightings_result.all.return_value = [(sighting, sighting_camera)]
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[alert_result, subject_result, sightings_result])

    with patch(
        "app.services.tracking_service._require_tracking_timeline_access",
        new=AsyncMock(),
    ):
        response = await get_tracking_timeline(
            db=db,
            alert_id=alert_id,
            claims={"id": str(uuid4())},
        )

    assert response.data is not None
    assert response.data.alert_id == alert_id
    assert response.data.sightings[0].camera_name == "Front Gate"
    assert response.data.sightings[0].sequence_no == 1
