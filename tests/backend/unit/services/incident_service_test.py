from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.models.alert import DetectionType
from app.services.incident_policy import (
    INCIDENT_MATCH_WINDOW_SECONDS,
    TRACKED_ALERT_DUPLICATE_WINDOW_SECONDS,
    tracked_alert_duplicate_stmt,
)
from app.services.tracking_service import next_tracking_sighting_sequence


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

@pytest.mark.asyncio
async def test_find_active_incident_for_embedding_compiles_correlated_alert_subquery():
    class Result:
        def first(self):
            return None

    class FakeDb:
        statement = None

        async def execute(self, statement):
            self.statement = statement
            # Compilation reproduces SQLAlchemy's auto-correlation validation
            # without requiring a live PostgreSQL connection.
            statement.compile(dialect=postgresql.dialect())
            return Result()

    db = FakeDb()
    observed_at = datetime.now(timezone.utc)
    result = await incident_service.find_active_incident_for_embedding(
        db=db,
        neighbourhood_id=uuid4(),
        embedding=[1.0] + [0.0] * 1279,
        embedding_model="test-model",
        observed_at=observed_at,
    )

    assert result is None
    compiled = db.statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert observed_at - timedelta(seconds=INCIDENT_MATCH_WINDOW_SECONDS) in compiled.params.values()
    assert observed_at + timedelta(seconds=INCIDENT_MATCH_WINDOW_SECONDS) in compiled.params.values()
    assert "FROM alert AS alert_1" in sql
    assert "alert_1.incident_id = incident.id" in sql


def test_tracked_duplicate_query_requires_same_active_recent_alert():
    now = datetime(2026, 10, 19, 8, 0, tzinfo=timezone.utc)
    statement = tracked_alert_duplicate_stmt(
        incident_id=uuid4(),
        camera_id=uuid4(),
        detection_type=DetectionType.HUMAN_PRESENCE,
        observed_at=now,
    )
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)

    assert "alert.detection_type" in sql
    assert "alert.status IN" in sql
    assert "alert.frame_timestamp >=" in sql
    assert "alert.frame_timestamp <=" in sql
    assert compiled.params["detection_type_1"] == DetectionType.HUMAN_PRESENCE
    assert now - timedelta(seconds=TRACKED_ALERT_DUPLICATE_WINDOW_SECONDS) in compiled.params.values()
    assert now in compiled.params.values()


@pytest.mark.asyncio
async def test_next_sighting_sequence_locks_subject_before_reading_maximum():
    subject_id = uuid4()

    class ScalarResult:
        def __init__(self, value):
            self.value = value

        def scalar_one_or_none(self):
            return self.value

        def scalar_one(self):
            return self.value

    class FakeDb:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(statement)
            if len(self.statements) == 1:
                return ScalarResult(subject_id)
            return ScalarResult(8)

    db = FakeDb()
    sequence = await next_tracking_sighting_sequence(db, subject_id)

    assert sequence == 8
    assert len(db.statements) == 2
    assert db.statements[0]._for_update_arg is not None
    assert "max(tracking_sighting.sequence_no)" in str(
        db.statements[1].compile(dialect=postgresql.dialect())
    )


@pytest.mark.asyncio
async def test_end_incident_waits_while_any_alert_is_active():
    incident_id = uuid4()
    alert = make_alert(datetime.now(timezone.utc))
    alert.incident_id = incident_id
    incident = SimpleNamespace(id=incident_id, ended_at=None)

    class CountResult:
        def scalar_one(self):
            return 1

    class FakeDb:
        async def get(self, model, identifier):
            return incident

        async def execute(self, statement):
            return CountResult()

    await incident_service.end_incident_if_no_active_alerts(
        db=FakeDb(),
        alert=alert,
        ended_at=datetime.now(timezone.utc),
    )

    assert incident.ended_at is None


@pytest.mark.asyncio
async def test_end_incident_when_no_alerts_remain_active():
    incident_id = uuid4()
    alert = make_alert(datetime.now(timezone.utc))
    alert.incident_id = incident_id
    incident = SimpleNamespace(id=incident_id, ended_at=None)
    ended_at = datetime.now(timezone.utc)

    class CountResult:
        def scalar_one(self):
            return 0

    class FakeDb:
        async def get(self, model, identifier):
            return incident

        async def execute(self, statement):
            return CountResult()

    await incident_service.end_incident_if_no_active_alerts(
        db=FakeDb(),
        alert=alert,
        ended_at=ended_at,
    )

    assert incident.ended_at == ended_at
