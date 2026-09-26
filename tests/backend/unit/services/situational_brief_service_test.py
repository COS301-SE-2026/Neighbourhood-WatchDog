from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.situational_brief_service import (
    _build_brief,
    _get_trigger,
    _require_brief_access,
    maybe_generate_situational_brief,
)


def make_sighting(
    *,
    sighting_id,
    camera,
    property_obj,
    sequence_no,
    observed_at,
    local_track_id,
    match_confidence,
):
    sighting = SimpleNamespace(
        id=uuid4(),
        local_track_id=9,
        observed_at=datetime.now(timezone.utc),
        sequence_no=1,
        match_confidence=0.95,
        clip_s3_key=None,
        clip_expires_at=None,
    )

    return sighting, camera, property_obj


def make_brief_context():
    subject_id = uuid4()
    alert_id = uuid4()

    source_camera = SimpleNamespace(
        id=uuid4(),
        name="Front Gate Camera",
        location="12 Main Street",
    )

    second_camera = SimpleNamespace(
        id=uuid4(),
        name="Parking Camera",
        location="14 Main Street",
    )

    source_property = SimpleNamespace(
        id=uuid4(),
        neighbourhood_id=uuid4(),
    )

    second_property = SimpleNamespace(
        id=uuid4(),
        neighbourhood_id=source_property.neighbourhood_id,
    )

    start = datetime(
        2026,
        9,
        21,
        10,
        0,
        tzinfo=timezone.utc,
    )

    subject = SimpleNamespace(
        id=subject_id,
        brief_data=None,
        brief_generated_at=None,
        brief_trigger=None,
    )

    alert = SimpleNamespace(
        id=alert_id,
        detection_type="HUMAN_PRESENCE",
        confidence_score=0.91,
        status="OPEN",
        frame_timestamp=start,
    )

    first_sighting = make_sighting(
        sighting_id=uuid4(),
        camera=source_camera,
        property_obj=source_property,
        sequence_no=1,
        observed_at=start,
        local_track_id=7,
        match_confidence=None,
    )

    second_sighting = make_sighting(
        sighting_id=uuid4(),
        camera=second_camera,
        property_obj=second_property,
        sequence_no=2,
        observed_at=start + timedelta(seconds=60),
        local_track_id=12,
        match_confidence=0.94,
    )

    return {
        "subject": subject,
        "alert": alert,
        "source_camera": source_camera,
        "source_property": source_property,
        "sightings": [
            first_sighting,
            second_sighting,
        ],
    }


def test_weapon_alert_reaches_severity_threshold_immediately():
    alert = SimpleNamespace(
        detection_type="WEAPON_DETECTED",
        frame_timestamp=datetime.now(timezone.utc),
    )

    assert _get_trigger(alert, []) == "severity_threshold"


def test_fall_alert_reaches_severity_threshold_immediately():
    alert = SimpleNamespace(
        detection_type="FALL_DETECTED",
        frame_timestamp=datetime.now(timezone.utc),
    )

    assert _get_trigger(alert, []) == "severity_threshold"


def test_duration_threshold_is_reached_after_sixty_seconds():
    start = datetime(
        2026,
        9,
        21,
        10,
        0,
        tzinfo=timezone.utc,
    )

    alert = SimpleNamespace(
        detection_type="HUMAN_PRESENCE",
        frame_timestamp=start,
    )

    sighting = SimpleNamespace(
        observed_at=start + timedelta(seconds=60),
    )

    camera = SimpleNamespace(id=uuid4())
    property_obj = SimpleNamespace(id=uuid4())

    sightings = [
        (sighting, camera, property_obj),
    ]

    assert _get_trigger(
        alert,
        sightings,
    ) == "duration_threshold"


def test_duration_threshold_is_not_reached_early():
    start = datetime(
        2026,
        9,
        21,
        10,
        0,
        tzinfo=timezone.utc,
    )

    alert = SimpleNamespace(
        detection_type="HUMAN_PRESENCE",
        frame_timestamp=start,
    )

    sighting = SimpleNamespace(
        observed_at=start + timedelta(seconds=30),
    )

    camera = SimpleNamespace(id=uuid4())
    property_obj = SimpleNamespace(id=uuid4())

    sightings = [
        (sighting, camera, property_obj),
    ]

    assert _get_trigger(
        alert,
        sightings,
    ) is None


def test_built_brief_contains_required_tracking_fields():
    context = make_brief_context()

    brief = _build_brief(
        tracking_subject=context["subject"],
        parent_alert=context["alert"],
        source_camera=context["source_camera"],
        source_property=context["source_property"],
        sightings=context["sightings"],
        trigger="duration_threshold",
    )

    assert brief.tracking_subject_id == context["subject"].id
    assert brief.trigger == "duration_threshold"

    assert len(brief.cameras) == 2
    assert len(brief.alerts) == 1
    assert len(brief.sightings) == 2

    assert brief.alerts[0].alert_id == context["alert"].id
    assert brief.alerts[0].detection_type == "HUMAN_PRESENCE"

    assert (
        brief.last_known_location.camera_id
        == context["sightings"][1][1].id
    )

    assert (
        brief.last_known_location.camera_name
        == "Parking Camera"
    )

    assert "Tracking subject" in brief.summary
    assert "Parking Camera" in brief.summary


@pytest.mark.asyncio
async def test_maybe_generate_persists_generated_brief():
    context = make_brief_context()

    subject_result = MagicMock()
    subject_result.one_or_none.return_value = (
        context["subject"],
        context["alert"],
        context["source_camera"],
        context["source_property"],
    )

    sightings_result = MagicMock()
    sightings_result.all.return_value = context["sightings"]

    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            subject_result,
            sightings_result,
        ]
    )
    db.commit = AsyncMock()

    brief = await maybe_generate_situational_brief(
        db=db,
        tracking_subject_id=context["subject"].id,
    )

    assert brief is not None
    assert brief.tracking_subject_id == context["subject"].id
    assert brief.trigger == "duration_threshold"

    assert context["subject"].brief_generated_at is not None
    assert context["subject"].brief_trigger == "duration_threshold"
    assert context["subject"].brief_data is not None

    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_resident_is_denied_brief_access():
    db = MagicMock()

    membership_result = MagicMock()
    membership_result.scalar_one_or_none.return_value = None

    db.execute = AsyncMock(
        return_value=membership_result,
    )

    resident_id = uuid4()
    neighbourhood_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await _require_brief_access(
            db=db,
            claims={
                "id": str(resident_id),
                "custom:role": "RESIDENT",
            },
            neighbourhood_id=neighbourhood_id,
        )

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "Only authorized officers can view situational briefs"
    )