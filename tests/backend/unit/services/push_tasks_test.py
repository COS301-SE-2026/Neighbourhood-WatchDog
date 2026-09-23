from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from firebase_admin import messaging

from app.tasks.push_tasks import send_push_to_users

class FakeAsyncSessionContext:
    """Stands in for 'async with WorkerSessionLocal() as db:' in tests."""

    def __init__(self, mock_db):
        self._mock_db = mock_db

    async def __aenter__(self):
        return self._mock_db

    async def aexist(self, exc_type, exc, tb):
        return False

def make_execute_mock(devices):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = devices
    return AsyncMock(return_value=mock_result)

def make_device(device_token="token=1"):
    return SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        device_token=device_token,
    )

class TestSendPushToUsers:
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.user_id = uuid4()
