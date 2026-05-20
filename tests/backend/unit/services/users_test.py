import pytest
from unittest.mock import Mock
from app.services.user_service import create_user

class TestCreateUser:
    def setup_method(self):
        """Runs before each test method - same as allt he other tests"""

        self.mock_db = Mock()
        
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()

        self.mock_user = Mock()
        self.mock_user.email = "test@email.com"
        self.mock_user.first_name = "John"
        self.mock_user.last_name = "Doe"
        self.mock_user.cognito_sub = "test-sub-123"

        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None

    @pytest.mark.asyncio
    async def test_happy_path(self):
        user = await create_user(
            email = "test@email.com",
            first_name = "John",
            last_name = "Doe",
            cognito_sub = "test-sub-123",
            db = self.mock_db
        )

        assert user is not None
        assert user.email == "test@email.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.commit.call_count == 1