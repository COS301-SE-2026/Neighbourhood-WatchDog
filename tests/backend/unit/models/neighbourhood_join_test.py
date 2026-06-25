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