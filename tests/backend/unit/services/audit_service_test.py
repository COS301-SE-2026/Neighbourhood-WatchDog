import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from app.services.audit_service import create_audit_log_item, get_audit_logs_handler
from app.models.audit_log import AuditAction, AuditLog
from app.models.user import UserRole
from uuid import uuid4
from datetime import datetime

OLD_EMAIL = "john@example.com"
NEW_EMAIL = "john@example.co.za"

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
        _ = create_audit_log_item(
            user_id=uuid4(),
            action=AuditAction.UPDATE,
            target_entity_type="USER",
            target_entity_id=uuid4(),
            old_values={
                "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "email": OLD_EMAIL,
                "first_name": "John",
                "last_name": "Doe",
                "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "role": UserRole.RESIDENT,
                "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "created_at": datetime.now()
            },
            new_values={
                "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                "email": NEW_EMAIL, #changed the email address
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
        user_id = uuid4()
        target_entity_id = uuid4()
        with pytest.raises(HTTPException) as exception:
            now = datetime.now()
            _ = create_audit_log_item(
                user_id=user_id,
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=target_entity_id,
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": now
                },
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
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
            user_id = None
            target_entity_id = uuid4()
            created_at = datetime.now()
            _ = create_audit_log_item(
                user_id=user_id,
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=target_entity_id,
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
                },
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL, #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
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
            user_id = uuid4()
            target_entity_id = uuid4()
            created_at = datetime.now()
            _ = create_audit_log_item(
                user_id=user_id,
                action=None,
                target_entity_type="USER",
                target_entity_id=target_entity_id,
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
                },
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL, #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_target_entity_type(self):
        user_id = uuid4()
        target_entity_type = None
        target_entity_id = uuid4()
        created_at = datetime.now()
        with pytest.raises(HTTPException) as exception:
            _ = create_audit_log_item(
                user_id=user_id,
                action=AuditAction.UPDATE,
                target_entity_type=target_entity_id,
                target_entity_id=target_entity_id,
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
                },
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL, #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_target_entity_id(self):
        user_id = uuid4()
        target_entity_id = None
        created_at = datetime.now()
        with pytest.raises(HTTPException) as exception:
            _ = create_audit_log_item(
                user_id=user_id,
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=target_entity_id,
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
                },
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL, #changed the email address
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
        user_id = uuid4()
        target_entity_id = uuid4()
        created_at = datetime.now()
        with pytest.raises(HTTPException) as exception:
            _ = create_audit_log_item(
                user_id=user_id,
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=target_entity_id,
                old_values=None,
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
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
            user_id = uuid4()
            target_entity_id = uuid4()
            created_at = datetime.now()
            _ = create_audit_log_item(
                user_id=user_id,
                action=AuditAction.UPDATE,
                target_entity_type="USER",
                target_entity_id=target_entity_id,
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
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
            _ = create_audit_log_item(
                user_id=uuid4(),
                action=AuditAction.CREATE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
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
        user_id = uuid4()
        target_entity_id = uuid4()
        created_at = datetime.now()
        with pytest.raises(HTTPException) as exception:
            _ = create_audit_log_item(
                user_id=user_id,
                action=AuditAction.DELETE,
                target_entity_type="USER",
                target_entity_id=target_entity_id,
                old_values=None,
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL, 
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": created_at
                },
                db=self.mock_db
            )

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.commit.call_count == 0

class TestGetAuditLogsHandler:
    def setup_method(self):
        """Runs before the test method"""

        self.mock_db = Mock()

        self.mock_log_item = Mock()
        self.mock_log_item.user_id = uuid4()
        self.mock_log_item.user_id = uuid4()

        self.mock_db.scalar.return_value = 5
        self.mock_db.scalars.return_value.all.return_value = {
            AuditLog(
                id=uuid4(),
                user_id=uuid4(),
                action=AuditAction.DELETE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
                timestamp=datetime.now(),
                old_values=None,
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL, 
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
            ),
            AuditLog(
                id=uuid4(),
                user_id=uuid4(),
                action=AuditAction.DELETE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
                timestamp=datetime.now(),
                old_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
                new_values={
                    "id" : "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL, #changed the email address
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now()
                },
            ),
        }
        
        self.total = 10
        self.page = 1
        self.size = 20

    #TODO: Happy case
    @pytest.mark.asyncio
    async def test_happy_case(self):
        
        get_audit_log_res = get_audit_logs_handler(
            page=self.page,
            size=self.size,
            db=self.mock_db
        )

        assert self.mock_db.scalars.return_value.all.call_count == 1
        assert self.mock_db.scalar.call_count == 1
        assert get_audit_log_res.status == 200

    @pytest.mark.asyncio
    async def test_offset_greater_than_total(self):
        #this line will make the total return 1
        self.mock_db.scalar.return_value = 1
        self.page = 21

        with pytest.raises(HTTPException) as exception:
            _ = get_audit_logs_handler(
                page=self.page,
                size=self.size,
                db=self.mock_db
            )

        assert exception.value.status_code == 422
        assert self.mock_db.scalars.return_value.all.call_count == 0
        assert self.mock_db.scalar.call_count == 1

    @pytest.mark.asyncio
    async def test_no_db(self):
        #this line will make the total return 1
        self.mock_db.scalar.return_value = 1
        self.page = 21

        with pytest.raises(HTTPException) as exception:
            _ = get_audit_logs_handler(
                page=self.page,
                size=self.size,
                db=None
            )

        assert exception.value.status_code == 500
        assert self.mock_db.scalars.return_value.all.call_count == 0
        assert self.mock_db.scalar.call_count == 0
