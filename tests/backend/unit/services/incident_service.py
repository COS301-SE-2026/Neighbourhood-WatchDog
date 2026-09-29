from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import incident_service


def make_alert(timestamp):
    return SimpleNamespace(
        id=uuid4(),
        camera_id=uuid4(),
        incident_id=None,
        frame_timestamp=timestamp,
        created_at=timestamp,
        detection_type="WEAPON_DETECTED",
        confidence_score=0.9,
        thumbnail_url=None,
        clip_s3_key=None,
        clip_expires_at=None,
        tracking_subject=None,
        processed=True,
        status="OPEN",
        resolved_by=None,
        resolved_at=None,
        camera=None,
    )


@pytest.mark.asyncio
async def test_create_incident_for_alert_attaches_alert():
    timestamp = datetime.now(timezone.utc)
    alert = make_alert(timestamp)

    class FakeDb:
        def __init__(self):
            self.added = []

        def add(self, value):
            self.added.append(value)

        async def flush(self):
            for value in self.added:
                if getattr(value, "id", None) is None:
                    value.id = uuid4()

    db = FakeDb()

    incident = await incident_service.create_incident_for_alert(
        db=db,
        alert=alert,
    )

    assert incident.id is not None
    assert incident.detection_type == "WEAPON_DETECTED"
    assert incident.started_at == timestamp
    assert incident.last_seen_at == timestamp
    assert alert.incident_id == incident.id
    assert alert.incident is incident


@pytest.mark.asyncio
async def test_ensure_incident_creates_one_for_legacy_alert():
    timestamp = datetime.now(timezone.utc)
    alert = make_alert(timestamp)

    class FakeDb:
        def __init__(self):
            self.added = []

        def add(self, value):
            self.added.append(value)

        async def flush(self):
            for value in self.added:
                if getattr(value, "id", None) is None:
                    value.id = uuid4()

        async def get(self, model, identifier):
            return None

    db = FakeDb()

    incident = await incident_service.ensure_incident_for_alert(
        db=db,
        alert=alert,
    )

    assert incident is not None
    assert alert.incident_id == incident.id


@pytest.mark.asyncio
async def test_ensure_incident_updates_last_seen():
    first_timestamp = datetime(2026, 9, 29, 8, 0, tzinfo=timezone.utc)
    second_timestamp = datetime(2026, 9, 29, 8, 0, 20, tzinfo=timezone.utc)

    incident_id = uuid4()

    alert = make_alert(second_timestamp)
    alert.incident_id = incident_id

    incident = SimpleNamespace(
        id=incident_id,
        started_at=first_timestamp,
        last_seen_at=first_timestamp,
        detection_type="WEAPON_DETECTED",
    )

    class FakeDb:
        async def get(self, model, identifier):
            return incident

    db = FakeDb()

    result = await incident_service.ensure_incident_for_alert(
        db=db,
        alert=alert,
    )

    assert result is incident
    assert incident.last_seen_at == second_timestamp