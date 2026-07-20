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
    base = {
        "id": uuid4(),
        "neighbourhood_id": uuid4(),
        "user_id": uuid4(),
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc),
    }
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

class TestJoinNeighbourhoodRes:
    def _make_nested_res(self) -> JoinRequestRes:
        return JoinRequestRes(**_make_join_request_res())

    def test_valid_response_with_data(self):
        """Happy path: all fields present"""
        nested = self._make_nested_res()
        res = JoinNeighbourhoodRes(
            status=201,
            message="Join request submitted",
            data=nested,
        )

        assert res.status == 201
        assert res.message == "Join request submitted"
        assert res.data is not None
        assert res.data.status == "PENDING"

    def test_only_status_required(self):
        """message and data are optional"""
        res = JoinNeighbourhoodRes(status=201)

        assert res.status == 201
        assert res.message is None
        assert res.data is None

    def test_error_response_without_data(self):
        """Error responses carry status and message only"""
        res = JoinNeighbourhoodRes(status=409, message="Already have a pending request")

        assert res.status == 409
        assert res.data is None

    def test_missing_status_raises_validation_error(self):
        with pytest.raises(ValidationError):
            JoinNeighbourhoodRes(message="oops")

    def test_invalid_nested_data_raises_validation_error(self):
        """Malformed data dict must be rejected"""
        with pytest.raises(ValidationError):
            JoinNeighbourhoodRes(status=201, data={"status": "PENDING"})

class TestResolveJoinRequestReq:
    def test_valid_approve_action(self):
        """APPROVE is a valid action"""
        req = ResolveJoinRequestReq(action="APPROVE")
        assert req.action == "APPROVE"

    def test_valid_deny_action(self):
        """DENY is a valid action"""
        req = ResolveJoinRequestReq(action="DENY")
        assert req.action == "DENY"

    def test_lowercase_approve_is_normalised(self):
        """Validator should uppercase the action so that lowercase input should pass"""
        req = ResolveJoinRequestReq(action="approve")
        assert req.action == "APPROVE"

    def test_lowercase_deny_is_normalised(self):
        """Lowercase deny should also be normalised"""
        req = ResolveJoinRequestReq(action="deny")
        assert req.action == "DENY"

    def test_mixed_case_is_normalised(self):
        """Mixed-case input should be uppercased and accepted"""
        req = ResolveJoinRequestReq(action="Approve")
        assert req.action == "APPROVE"

    def test_invalid_action_raises_validation_error(self):
        """Unknown action strings must be rejected"""
        with pytest.raises(ValidationError):
            ResolveJoinRequestReq(action="IGNORE")

    def test_empty_action_raises_validation_error(self):
        """Empty string is not a valid action"""
        with pytest.raises(ValidationError):
            ResolveJoinRequestReq(action="")

    def test_none_action_raises_validation_error(self):
        """None is not a valid action"""
        with pytest.raises(ValidationError):
            ResolveJoinRequestReq(action=None)

    def test_missing_action_raises_validation_error(self):
        """action is required"""
        with pytest.raises(ValidationError):
            ResolveJoinRequestReq()

class TestResolveJoinRequestRes:
    def _make_nested_res(self, status: str = "APPROVED") -> JoinRequestRes:
        return JoinRequestRes(**_make_join_request_res(status=status))

    def test_valid_approved_response(self):
        """Happy path: request was approved"""
        nested = self._make_nested_res("APPROVED")
        res = ResolveJoinRequestRes(
            status=200,
            message="Request approved",
            data=nested,
        )

        assert res.status == 200
        assert res.data.status == "APPROVED"

    def test_valid_denied_response(self):
        """Happy path: request was denied"""
        nested = self._make_nested_res("DENIED")
        res = ResolveJoinRequestRes(
            status=200,
            message="Request denied",
            data=nested,
        )

        assert res.data.status == "DENIED"

    def test_only_status_required(self):
        """message and data are optional"""
        res = ResolveJoinRequestRes(status=200)

        assert res.message is None
        assert res.data is None

    def test_error_response_without_data(self):
        """e.g. 404 when the request was not found"""
        res = ResolveJoinRequestRes(status=404, message="Request not found")

        assert res.status == 404
        assert res.data is None

    def test_missing_status_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ResolveJoinRequestRes(message="oops")

    def test_invalid_nested_data_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ResolveJoinRequestRes(status=200, data={"status": "APPROVED"})
