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