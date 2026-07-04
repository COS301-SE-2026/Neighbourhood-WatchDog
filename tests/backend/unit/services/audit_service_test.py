import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from app.services.audit_service import create_audit_log_item
from app.models.audit_log import AuditAction
from app.models.user import UserRole
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
            action=AuditAction.CREATE,
            target_entity_type="USER",
            target_entity_id=uuid4(),
            ip_address="196.168.21.2",
            timestamp=datetime.now(),
            old_values={
                "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "role": UserRole.RESIDENT,
                "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "created_at": datetime.now()
            },
            new_value={
                "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "email": "john@example.co.za", #changed the email address
                "first_name": "John",
                "last_name": "Doe",
                "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "role": UserRole.RESIDENT,
                "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "created_at": datetime.now()
            }
        )

        assert self.mock_mb.add.call_count == 1
        assert self.mock_mb.refresh.call_count == 1
        assert self.mock_mb.commit.call_count == 1
        assert self.mock_db.rollback.call_count == 0


        #TODO: include a case where the same new and old values are passed