import pytest
from fastapi import HTTPException
from unittest.mock import Mock, AsyncMock
from app.services.audit_service import create_audit_log_item, get_audit_logs_handler
from app.models.audit_log import AuditAction, AuditLog
from app.models.user import UserRole
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select

from app.services import audit_service as audit_service_module

OLD_EMAIL = "john@example.com"
NEW_EMAIL = "john@example.co.za"

class TestCreateAuditLogItem:
    def setup_method(self):
        """Runs before the test method"""

        self.mock_db = Mock()
        self.mock_db.add = Mock()
        self.mock_db.commit = AsyncMock()

        self.mock_log_item = Mock()
        self.mock_log_item.user_id = uuid4()
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None


    @pytest.mark.asyncio
    async def test_happy_path(self):
        _ = await create_audit_log_item(
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

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0

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

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0

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

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0

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

        assert exception.value.status_code == 400
        assert self.mock_db.add.call_count == 0

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
                    "email": NEW_EMAIL,
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
                    "email": NEW_EMAIL, 
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

class TestGetAuditLogsHandler:
    def setup_method(self):
        """Runs before the test method"""

        self.mock_db = Mock()
        self.mock_db.execute = AsyncMock()

        self.audit_logs = [
            AuditLog(
                id=uuid4(),
                user_id=uuid4(),
                action=AuditAction.DELETE,
                target_entity_type="USER",
                target_entity_id=uuid4(),
                timestamp=datetime.now(),
                old_values=None,
                new_values={
                    "id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now(),
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
                    "id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": OLD_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now(),
                },
                new_values={
                    "id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "email": NEW_EMAIL,
                    "first_name": "John",
                    "last_name": "Doe",
                    "cognito_sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                    "role": UserRole.RESIDENT,
                    "neighbourhood_id": "f4b3e8c9-2d10-4f5c-b17a-59368dca86b2",
                    "created_at": datetime.now(),
                },
            ),
        ]

        # Result of: count_result = await db.execute(count_stmt)
        self.count_result = Mock()
        self.count_result.scalar_one.return_value = len(self.audit_logs)

        # Result of: logs_result = await db.execute(stmt)
        self.logs_result = Mock()
        self.logs_result.scalars.return_value.all.return_value = self.audit_logs

        self.page = 1
        self.size = 20

    #TODO: Happy case
    @pytest.mark.asyncio
    async def test_happy_case(self):

        self.mock_db.execute.side_effect = [
            self.count_result,
            self.logs_result,
        ]

        get_audit_log_res = await get_audit_logs_handler(
            page=self.page,
            size=self.size,
            db=self.mock_db
        )

        assert get_audit_log_res.status == 200
        assert self.mock_db.execute.await_count == 2
        self.count_result.scalar_one.assert_called_once()
        self.logs_result.scalars.return_value.all.assert_called_once()

    @pytest.mark.asyncio
    async def test_offset_greater_than_total(self):
        #this line will make the total return 1
        self.mock_db.scalar.return_value = 1
        self.mock_db.execute.side_effect = [self.count_result]
        self.page = 21

        with pytest.raises(HTTPException) as exception:
            await get_audit_logs_handler(
                page=self.page,
                size=self.size,
                db=self.mock_db
            )

        assert exception.value.status_code == 422
        assert self.mock_db.execute.await_count == 1
        self.count_result.scalar_one.assert_called_once()
        self.logs_result.scalars.return_value.all.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_db(self):
        with pytest.raises(HTTPException) as exception:
            await get_audit_logs_handler(
                page=self.page,
                size=self.size,
                db=None
            )

        assert exception.value.status_code == 500
        self.mock_db.execute.assert_not_awaited()


def test_validate_action_values_supports_delete():
    old_values = {"email": "old@example.com"}
    new_values = {"email": "new@example.com"}

    returned_old, returned_new = (
        audit_service_module._validate_action_values(
            AuditAction.DELETE,
            old_values,
            new_values,
        )
    )

    assert returned_old == old_values
    assert returned_new is None


def test_validate_action_values_returns_values_for_unknown_action():
    old_values = {"before": True}
    new_values = {"after": True}

    returned_old, returned_new = (
        audit_service_module._validate_action_values(
            "UNKNOWN_ACTION",
            old_values,
            new_values,
        )
    )

    assert returned_old == old_values
    assert returned_new == new_values


@pytest.mark.parametrize(
    ("page", "size", "detail"),
    [
        (0, 30, "page must be >= 1"),
        (1, 0, "size must be >= 1"),
    ],
)
def test_validate_pagination_rejects_invalid_values(page, size, detail):
    with pytest.raises(HTTPException) as exc_info:
        audit_service_module._validate_pagination(page, size)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == detail


def test_apply_filters_applies_search_action_and_date_filters():
    statement = select(AuditLog)
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 12, 31)

    filtered = audit_service_module._apply_filters(
        statement,
        search_term="camera",
        action=AuditAction.DELETE,
        start_date=start_date,
        end_date=end_date,
    )

    assert filtered is not statement

    compiled_sql = str(filtered)
    assert "audit_log" in compiled_sql
def test_validate_action_values_supports_create():
    new_values = {
        "email": "created@example.com",
        "role": "RESIDENT",
    }

    returned_old, returned_new = (
        audit_service_module._validate_action_values(
            AuditAction.CREATE,
            old_values=None,
            new_values=new_values,
        )
    )

    assert returned_old is None
    assert returned_new == new_values