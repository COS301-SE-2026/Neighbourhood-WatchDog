import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from app.services.audit_service import create_audit_log_item

class TestCreateAuditLogItem:
    def setup_method(self):
        """Runs before the test method"""

        self.mock_db = Mock()
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()

        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None

    