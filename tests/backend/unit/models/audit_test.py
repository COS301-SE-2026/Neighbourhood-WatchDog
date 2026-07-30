from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.audit_log import GetAuditLogsRes, AuditLogScheme, PaginatedResponse
from app.models.audit_log import AuditAction

def _audit_log_res(**overrides):
    base = {
        "id": uuid4(),
        "user_id": uuid4(),
        "action": list(AuditAction)[0],
        "target_entity_type": "camera",
        "target_entity_id": uuid4(),
        "timestamp": datetime.now(timezone.utc),
        "old_values": {"enabled": False},
        "new_values": {"enabled": True},
    }
    base.update(overrides)
    return base

class TestAuditlogScheme:
    def test_valid_fields(self):
        data = _audit_log_res()
        res = AuditLogScheme(**data)

        assert res.id == data["id"]
        assert res.user_id == data["user_id"]
        assert res.action == data["action"]
        assert res.target_entity_type == data["target_entity_type"]
        assert res.target_entity_id == data["target_entity_id"]
        assert res.timestamp == data["timestamp"]
        assert res.old_values == data["old_values"]
        assert res.new_values  == data["new_values"]

    def test_missing_id_raises(self):
        data = _audit_log_res()
        del data["id"]

        with pytest.raises(ValidationError):
            AuditLogScheme(**data)

    def test_missing_user_id_raises(self):
        data = _audit_log_res()
        del data["user_id"]

        with pytest.raises(ValidationError):
            AuditLogScheme(**data)

    def test_missing_action_raises(self):
        data = _audit_log_res()
        del data["action"]

        with pytest.raises(ValidationError):
            AuditLogScheme(**data)

    def test_missing_timestamp_raises(self):
        data = _audit_log_res()
        del data["timestamp"]

        with pytest.raises(ValidationError):
            AuditLogScheme(**data)

    def test_invalid_action_raises(self):
        data = _audit_log_res(action="NOT_A_REAL_ACTION")
        del data["timestamp"]

        with pytest.raises(ValidationError):
            AuditLogScheme(**data)

    def test_optional_fields_default_to_none(self):
        data = _audit_log_res()
        del data["target_entity_type"]
        del data["target_entity_id"]
        del data["old_values"]
        del data["new_values"]

        res = AuditLogScheme(**data)

        assert res.target_entity_type is None
        assert res.target_entity_id is None
        assert res.old_values is None
        assert res.new_values is None

    def test_from_attributes_config_present(self):
        """model_config should allow construction from ORM objects"""
        assert AuditLogScheme.model_config.get("from_attributes") is True

class TestGetAuditLogres:
    def _make_nested_data(self) -> PaginatedResponse[AuditLogScheme]:
        return PaginatedResponse[AuditLogScheme](
            total=1, page=1, size=30, results=[AuditLogScheme(**_audit_log_res())]
        )

    def test_valid_response_with_data(self):
        res = GetAuditLogsRes(
            status=200,
            message="Audit logs retrieved successfully",
            data=self._make_nested_data(),
        )

        assert res.status == 200
        assert res.data.total == 1

    def test_message_defaults_to_none(self):
        res = GetAuditLogsRes(status=200, data=self._make_nested_data())
        assert res.message is None

    def test_missing_status_raises(self):
        with pytest.raises(ValidationError):
            GetAuditLogsRes(message="oops", data=self._make_nested_data())

    def test_missing_data_raises(self):
        with pytest.raises(ValidationError):
            GetAuditLogsRes(status=200, message="ok")

    def test_invlaid_nested_data_raises(self):
        with pytest.raises(ValidationError):
            GetAuditLogsRes(
                status=200,
                message="ok",
                data={"total": "not-an-int", "page": 1, "size": 30, "results": []},
            )

class TestPaginatedRes:
    def _make_log(self) -> AuditLogScheme:
        return AuditLogScheme(**_audit_log_res())

    def test_valid_fields(self):
        res = PaginatedResponse[AuditLogScheme](
            total=1,
            page=1,
            size=30,
            results=[self._make_log()],
        )

        assert res.total == 1
        assert res.page == 1
        assert res.size == 30
        assert len(res.results) == 1

    def test_missing_total_raises(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[AuditLogScheme](page=1, size=30, results=[])

    def test_missing_page_raises(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[AuditLogScheme](total=1, size=30, results=[])

    def test_missing_size_raises(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[AuditLogScheme](total=1, page=1, results=[])

    def test_missing_results_raises(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[AuditLogScheme](total=1, page=1, size=30)

    def test_empty_results_list_is_allowed(self):
        res = PaginatedResponse[AuditLogScheme](total=0, page=1, size=30, results=[])
        assert res.results == []

    def test_invalid_itemin_results_raises(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[AuditLogScheme](
                total=1,
                page=1,
                size=30,
                results=[{**_audit_log_res(), "id": "not-a-uuid"}],
            )

    