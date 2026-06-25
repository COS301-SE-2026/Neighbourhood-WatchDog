from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.neighbourhood_join import (
    JoinNeighbourhoodReq,
    JoinRequestRes,
    JoinNeighbourhoodRes,
    ResolveJoinRequestReq,
    ResolveJoinRequestRes,
)

def _make_join_request_res(**overrides):
    base = dict(
        id=uuid4(),
        neighbourhood_id=uuid4(),
        user_id=uuid4(),
        status="PENDING",
        created_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return base
class TestJoinNeighbourhoodReq:
    def test_valid_join_code(self):
        """Happy path: normal alphanumeric join code"""
        req = JoinNeighbourhoodReq(join_code="ABC12345")
        assert req.join_code == "ABC12345"

    def test_whitespace_is_stripped(self):
        """Leading/trailing whitespace should be stripped and still pass"""
        req = JoinNeighbourhoodReq(join_code="  XYZ999  ")
        assert req.join_code == "XYZ999"

    def test_empty_string_raises_validation_error(self):
        """An empty join_code must be rejected"""
        with pytest.raises(ValidationError):
            JoinNeighbourhoodReq(join_code="")

    def test_whitespace_only_raises_validation_error(self):
        """Whitespace-only string collapses to empty after stripping and must be rejected"""
        with pytest.raises(ValidationError):
            JoinNeighbourhoodReq(join_code="   ")

    def test_none_join_code_raises_validation_error(self):
        """None is not a valid join_code"""
        with pytest.raises(ValidationError):
            JoinNeighbourhoodReq(join_code=None)

    def test_missing_join_code_raises_validation_error(self):
        """join_code is required"""
        with pytest.raises(ValidationError):
            JoinNeighbourhoodReq()

class TestJoinRequestRes:
    def test_valid_pending_request(self):
        """Happy path: all required fields, status PENDING"""
        data = _make_join_request_res()
        res = JoinRequestRes(**data)

        assert res.id == data["id"]
        assert res.neighbourhood_id == data["neighbourhood_id"]
        assert res.user_id == data["user_id"]
        assert res.status == "PENDING"
        assert res.created_at == data["created_at"]

    def test_approved_status_accepted(self):
        """Status can be APPROVED"""
        res = JoinRequestRes(**_make_join_request_res(status="APPROVED"))
        assert res.status == "APPROVED"

    def test_denied_status_accepted(self):
        """Status can be DENIED"""
        res = JoinRequestRes(**_make_join_request_res(status="DENIED"))
        assert res.status == "DENIED"

    def test_missing_id_raises_validation_error(self):
        data = _make_join_request_res()
        del data["id"]

        with pytest.raises(ValidationError):
            JoinRequestRes(**data)

    def test_missing_neighbourhood_id_raises_validation_error(self):
        data = _make_join_request_res()
        del data["neighbourhood_id"]

        with pytest.raises(ValidationError):
            JoinRequestRes(**data)

    def test_missing_user_id_raises_validation_error(self):
        data = _make_join_request_res()
        del data["user_id"]

        with pytest.raises(ValidationError):
            JoinRequestRes(**data)

    def test_missing_status_raises_validation_error(self):
        data = _make_join_request_res()
        del data["status"]

        with pytest.raises(ValidationError):
            JoinRequestRes(**data)

    def test_missing_created_at_raises_validation_error(self):
        data = _make_join_request_res()
        del data["created_at"]

        with pytest.raises(ValidationError):
            JoinRequestRes(**data)

    def test_invalid_uuid_for_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            JoinRequestRes(**_make_join_request_res(id="not-a-uuid"))

    def test_invalid_uuid_for_neighbourhood_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            JoinRequestRes(**_make_join_request_res(neighbourhood_id="bad"))

    def test_invalid_uuid_for_user_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            JoinRequestRes(**_make_join_request_res(user_id="bad"))

    def test_from_attributes_config_present(self):
        """model_config should allow construction from ORM objects"""
        assert JoinRequestRes.model_config.get("from_attributes") is True