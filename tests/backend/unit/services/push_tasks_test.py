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
