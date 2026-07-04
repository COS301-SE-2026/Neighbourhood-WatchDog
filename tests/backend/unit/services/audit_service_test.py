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
            action=AuditAction.UPDATE,
            target_entity_type="USER",
            target_entity_id=uuid4(),
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
            new_values={
                "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "email": "john@example.co.za", #changed the email address
                "first_name": "John",
                "last_name": "Doe",
                "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "role": UserRole.RESIDENT,
                "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "created_at": datetime.now()
            },
            db=self.mock_db
        )

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_same_old_new_values(self):
        with pytest.raises(HTTPException) as exception:
            now = datetime.now()
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": now
                },
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": now
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_user_id(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=None,
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
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
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.co.za", #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_action(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=None,
                target_entity_type="USER",
                target_entity_id=uuid4(),
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
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.co.za", #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_target_entity_type(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.UPDATE,
                target_entity_type=None,
                target_entity_id=uuid4(),
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
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.co.za", #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_target_entity_id(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=None,
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
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.co.za", #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_update_empty_old(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
                old_values=None,
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.co.za", #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_update_empty_new(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
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
                new_values=None,
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_create_empty_new(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.CREATE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
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
                new_values=None,
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_delete_empty_old(self):
        with pytest.raises(HTTPException) as exception:
            _ = await create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.DELETE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
                old_values=None,
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": "john@example.co.za", #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0