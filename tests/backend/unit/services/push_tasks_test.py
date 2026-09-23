from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


from app.tasks.push_tasks import send_push_to_users

class FakeAsyncSessionContext:
    """Stands in for 'async with WorkerSessionLocal() as db:' in tests."""

    def __init__(self, mock_db):
        self._mock_db = mock_db

    async def __aenter__(self):
        return self._mock_db

    async def __aexit__(self, exc_type, exc, tb):
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
        self.user_id = uuid4()

    def test_returns_early_for_empty_user_ids(self):
        with patch(
            "app.tasks.push_tasks.WorkerSessionLocal",
            return_value=FakeAsyncSessionContext(self.mock_db),
        ) as worker_session:
            send_push_to_users([], "title", "body", None)

        worker_session.assert_not_called()
        self.mock_db.execute.assert_not_called()

    def test_sends_to_all_devices_and_commits(self):
        device_one = make_device("token-1")
        device_two = make_device("token-2")
        self.mock_db.execute = make_execute_mock([device_one, device_two])

        with (
            patch(
                "app.tasks.push_tasks.WorkerSessionLocal",
                return_value=FakeAsyncSessionContext(self.mock_db),
            ),
            patch ("app.tasks.push_tasks.messaging.send") as mock_send,
        ):
            send_push_to_users(
                [str(self.user_id)], 
                "New alert", 
                "HUMAN_PRESENCE detected", 
                {"alert_id": "abc"}
            )

        assert mock_send.call_count == 2
        sent_tokens = {call.args[0].token for call in mock_send.call_args_list}
        assert sent_tokens == {"token-1", "token-2"}

        assert self.mock_db.execute.await_count == 1
        self.mock_db.commit.assert_awaited_once()
