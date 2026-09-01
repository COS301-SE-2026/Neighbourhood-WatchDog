from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from app.tasks.risk_score_tasks import recalculate_all_risk_scores, calculate_risk_score_task

class FakeAsyncSessionContext:
    """Stands in for 'async with SessionLocal() as db:' in tests
        
        SessionLocal() returns this object entering the 'async with' block
        hands back the mock db and exiting calls db.close() the same was AsyncSessions own __aexit__ would"""
    def __init__(self, mock_db):
        self._mock_db = mock_db

    async def __aenter__(self):
        return self._mock_db

    async def __aexit__(self, exc_type, exc, tb):
        await self._mock_db.close()
        return False

def make_execute_mock(scalars_all_return_value):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = scalars_all_return_value
    return AsyncMock(return_value=mock_result)
    
class TestRecalculateAllRiskScores:
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.mock_db.execute = AsyncMock()
        self.mock_db.close = AsyncMock()
    
    def test_delay_call_per_neighbourhood(self):
        neighbourhood_ids = [uuid4(), uuid4(), uuid4(), uuid4()]
        self.mock_db.execute = make_execute_mock(neighbourhood_ids)

        with patch(
            'app.tasks.risk_score_tasks.WorkerSessionLocal', 
            return_value=FakeAsyncSessionContext(self.mock_db)
        ), patch('app.tasks.risk_score_tasks.calculate_risk_score_task') as mock_task:

            recalculate_all_risk_scores()

            assert mock_task.delay.call_count == 4
            for nid in neighbourhood_ids:
                mock_task.delay.assert_any_call(str(nid))
            assert self.mock_db.close.call_count == 1

    def test_delay_call_no_neighbourhood(self):
        neighbourhood_ids = []
        self.mock_db.execute = make_execute_mock(neighbourhood_ids)
        with patch(
            'app.tasks.risk_score_tasks.WorkerSessionLocal', 
            return_value=FakeAsyncSessionContext(self.mock_db)
        ), patch('app.tasks.risk_score_tasks.calculate_risk_score_task') as mock_task:

            recalculate_all_risk_scores()

            assert mock_task.delay.call_count == 0
            assert self.mock_db.close.call_count == 1

class TestCalculateRiskScoreTask:
    def setup_method(self):
        self.mock_db = AsyncMock()
        self.mock_db.rollback = AsyncMock()
        self.mock_db.close = AsyncMock()
        self.neighbourhood_id = uuid4()

    def test_calculate_risk_score(self):
        with patch(
            'app.tasks.risk_score_tasks.WorkerSessionLocal', 
            return_value = FakeAsyncSessionContext(self.mock_db)
        ), patch('app.tasks.risk_score_tasks.calculate_risk_score_handler') as mock_handler:

            calculate_risk_score_task(str(self.neighbourhood_id))

            assert mock_handler.call_count == 1

            mock_handler.assert_called_once_with(self.neighbourhood_id, self.mock_db)
            assert self.mock_db.rollback.call_count == 0
            assert self.mock_db.close.call_count == 1

    def test_exception_roll_back(self):
        with patch(
            'app.tasks.risk_score_tasks.WorkerSessionLocal', 
            return_value=FakeAsyncSessionContext(self.mock_db)
        ), patch('app.tasks.risk_score_tasks.calculate_risk_score_handler', side_effect=Exception("fail")):

            calculate_risk_score_task(str(self.neighbourhood_id))

            assert self.mock_db.rollback.call_count == 1
            assert self.mock_db.close.call_count == 1