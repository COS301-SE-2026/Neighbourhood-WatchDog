import pytest
from unittest.mock import Mock
from datetime import datetime
from uuid import uuid4

from app.models.risk_score_history import RiskLevel
from app.services.risk_score_history_service import get_neighbourhood_score_handler

class TestGetNeighbourhoodScore:
    def setup_method(self):
        self.mock_db = Mock()
        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id" : str(self.neighbourhood_id)}

        self.mock_risk_score = Mock()
        self.mock_risk_score.id = uuid4()
        self.mock_risk_score.neighbourhood_id = self.neighbourhood_id
        self.mock_risk_score.score = 214
        self.mock_risk_score.classification = RiskLevel.HIGH
        self.mock_risk_score.alert_count = 19
        self.mock_risk_score.calculated_at = datetime.now()

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [self.mock_risk_score]


        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

    def reset_side_effects(self, neighbourhood_risk_history=None):
        """Helper to reset side_effect between tests"""
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [neighbourhood_risk_history]

    @pytest.mark.asyncio
    async def test_happy_path(self):
        risk_score = get_neighbourhood_score_handler(
            self.neighbourhood_id,
            self.mock_db,
            self.mock_claims
        )

        assert risk_score.neighbourhood_id == self.neighbourhood_id
        assert risk_score.alert_count == 19
        assert risk_score.classification == RiskLevel.HIGH
        assert risk_score.score == 214

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0