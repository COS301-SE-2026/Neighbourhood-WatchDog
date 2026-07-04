import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction
from uuid import uuid4
from datetime import datetime

class TestCreateAuditLogItem:
    def setup_method(self):
        """Runs before the test method"""

        self.mock_db = Mock()
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()

        self.mock_log_item = Mock()
        self.mock_log_item.user_id = uuid4()
        self.mock_log_item.user_id = uuid4()

        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None

    @pytest.mark.asyncio
    async def test_happy_path(self):
        audit_log_item = await create_audit_log_item(
            user_id=uuid4(),
            action=AuditAction.LOGIN,
            target_entity_type="TYPE",
            target_entity_id=uuid4(),
            ip_address="196.168.21.2",
            timestamp=datetime.now(),
            extra_metadata=(
                {"old-value" : {"name": "John"}, "new-value": {"name" : "James"}}
            )
        )

        assert self.mock_mb.add.call_count == 1
        assert self.mock_mb.refresh.call_count == 1
        assert self.mock_mb.commit.call_count == 1
        assert self.mock_db.rollback.call_count == 0