from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.dispatch import DispatchStatus
from app.models.security_officer import AvailabilityStatus
from app.schemas.dispatch import AlertDispatchRes, DispatchCandidateRes, DispatchNotificationRes, RespondDispatchReq, RespondDispatchRes

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

def make_candidate(**overrides):
    kwargs = dict(
        id=uuid4(),
        alert_id=uuid4(),
        officer_id=uuid4(),
        rank=1,
        score=2.5,
        distance=800.0,
        eta=120.0,
        workload=0,
        status=DispatchStatus.SELECTED,
        officer_availability=AvailabilityStatus.AVAILABLE,
        is_location_stale=False,
        created_at=NOW,
        notified_at=None,
        responded_at=None,
    )
    kwargs.update(overrides)
    return kwargs

class TestDispatchCandidateRes:
    def test_valid_model(self):
        """happy path"""
        kwargs = make_candidate()
        candidate = DispatchCandidateRes(**kwargs)

        assert candidate.id == kwargs["id"]
        assert candidate.officer_id == kwargs["officer_id"]
        assert candidate.rank == 1
        assert candidate.score == 2.5
        assert candidate.distance == 800.0
        assert candidate.eta == 120.0
        assert candidate.status == DispatchStatus.SELECTED
        assert candidate.is_location_stale is False

    def test_no_candidate_has_no_fields(self):
        candidate = DispatchCandidateRes(
            **make_candidate(
                officer_id=None,
                rank=None,
                score=None,
                distance=None,
                eta=None,
                workload=None,
                status=DispatchStatus.NO_CANDIDATE,
                officer_availability=None,
            )
        )
        assert candidate.officer_id is None
        assert candidate.rank == None
        assert candidate.score == None
        assert candidate.status == DispatchStatus.NO_CANDIDATE

    def test_invalid_status_raises(self):
        candidate = make_candidate(status="LUNCH")
        with pytest.raises(ValidationError):
            DispatchCandidateRes(**candidate)

    def test_invalid_availability_raises(self):
        candidate = make_candidate(officer_availability="ON_A_BREAK")
        with pytest.raises(ValidationError):
            DispatchCandidateRes(**candidate)

    def test_invalid_uuid_raises(self):
        candidate = make_candidate(alert_id="not-a-uuid")
        with pytest.raises(ValidationError):
            DispatchCandidateRes(**candidate)

    def test_missing_required_field_raises(self):
        for missing in ["id", "alert_id", "status", "is_location_stale", "created_at"]:
            candidate = make_candidate()
            del candidate[missing]
            with pytest.raises(ValidationError):
                DispatchCandidateRes(**candidate)

class TestAlertDispatchRes:
    def test_default_values_ok(self):
        """Only alert_id required"""
        alert_id = uuid4()
        res = AlertDispatchRes(alert_id=alert_id)

        assert res.alert_id == alert_id
        assert res.selected is None
        assert res.pending == []
        assert res.queued == []
        assert res.no_candidate is False

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            AlertDispatchRes()

    def test_selected_pending_queued(self):
        alert_id = uuid4()
        selected = DispatchCandidateRes(**make_candidate(alert_id=alert_id))
        pending = DispatchCandidateRes(**make_candidate(alert_id=alert_id, rank=2, status=DispatchStatus.PENDING))
        queued = DispatchCandidateRes(
            **make_candidate(
                alert_id=alert_id, 
                rank=3, 
                status=DispatchStatus.QUEUED, 
                officer_availability=AvailabilityStatus.BUSY
            )
        )

        res = AlertDispatchRes(
            alert_id=alert_id,
            selected=selected,
            pending=[pending],
            queued=[queued],
        )

        assert res.selected == selected
        assert res.pending == [pending]
        assert res.queued == [queued]
        assert res.no_candidate is False

    def test_no_candidate(self):
        res = AlertDispatchRes(alert_id=uuid4(), no_candidate=True)
        assert res.no_candidate is True
        assert res.selected is None

    def test_invalid_pending_raises(self):
        with pytest.raises(ValidationError):
            AlertDispatchRes(alert_id=uuid4(), pending=["not-a-candidate"])

class TestRespondDispatchReq:
    def test_accept(self):
        req = RespondDispatchReq(action="ACCEPT")
        assert req.action == "ACCEPT"
 
    def test_decline(self):
        req = RespondDispatchReq(action="DECLINE")
        assert req.action == "DECLINE"
 
    def test_lowercase_raises(self):
        with pytest.raises(ValidationError):
            RespondDispatchReq(action="accept")
 
    def test_invalid_raises(self):
        with pytest.raises(ValidationError):
            RespondDispatchReq(action="MAYBE")
 
    def test_missing_raises(self):
        with pytest.raises(ValidationError):
            RespondDispatchReq()
 
    def test_none_raises(self):
        with pytest.raises(ValidationError):
            RespondDispatchReq(action=None)

class TestRespondDispatchRes:
    def test_with_data(self):
        data = DispatchCandidateRes(**make_candidate(status=DispatchStatus.ACCEPTED))
        res = RespondDispatchRes(status=200, message="Dispatch accepted", data=data)
        assert res.status == 200
        assert res.message == "Dispatch accepted"
        assert res.data == data

    def test_missing_status_raises(self):
        with pytest.raises(ValidationError):
            RespondDispatchRes(message="Dispatch accepted", data=None)