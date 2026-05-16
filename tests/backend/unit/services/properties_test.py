import pytest
from unittest.mock import Mock
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

# create_property_handler tests
class TestCreateProper:
    def setup_method(self):
        """Runs before each test method"""
        self.mock_db = Mock()

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        claims = {
            "sub": "cognito-sub-123"
        }

        self.mock_db.add() = Mock()
        self.mock_db.flush() = Mock()
        self.mock_db.commit() = Mock()
        self.mock_db.rollback() = Mock()

        self.mock_db.flush() = Mock(side_effect=IntegrityError("error", "params", "origin"))
        self.mock_db.rollback() = Mock()
