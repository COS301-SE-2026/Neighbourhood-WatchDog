import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.tasks.risk_score_tasks import recalculate_all_risk_scores, calculate_risk_score_task

class TestRecalculateAllRiskScores:
    def setup_method(self):
        self.mock_db = Mock()
    
    def test_delay_call_per_neighbourhood(self):
        neighbourhood_ids = [uuid4(), uuid4(), uuid4(), uuid4()]
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = neighbourhood_ids
        with patch('app.tasks.risk_score_tasks.SessionLocal', return_value=self.mock_db), \
            patch('app.tasks.risk_score_tasks.calculate_risk_score_task') as mock_task:

            recalculate_all_risk_scores()

            assert mock_task.delay.call_count == 4
            for nid in neighbourhood_ids:
                mock_task.delay.assert_any_call(str(nid))
            assert self.mock_db.close.call_count == 1

    def test_delay_call_no_neighbourhood(self):
        neighbourhood_ids = []
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = neighbourhood_ids
        with patch('app.tasks.risk_score_tasks.SessionLocal', return_value=self.mock_db), \
            patch('app.tasks.risk_score_tasks.calculate_risk_score_task') as mock_task:

            recalculate_all_risk_scores()

            assert mock_task.delay.call_count == 0
            assert self.mock_db.close.call_count == 1