import pytest
from unittest.mock import Mock
from datetime import datetime
from uuid import uuid4

from app.models.risk_score_history import RiskLevel

class TestGetNeighbourhoodScore:
    def setup_method(self):
        self.mock_db = Mock()
        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id" : str(self.neighbourhood_id)}

        self.mock_risk_score_history = Mock()
        self.mock_risk_score_history.id = uuid4()
        self.mock_risk_score_history.neighbourhood_id = self.neighbourhood_id
        self.mock_risk_score_history.score = 214
        self.mock_risk_score_history.classification = RiskLevel.HIGH
        self.mock_risk_score_history.alert_count = 19
        self.mock_risk_score_history.calculated_at = datetime.now()

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [self.mock_risk_score_history]


        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

    def reset_side_effects(self, neighbourhood_risk_history=None):
        """Helper to reset side_effect between tests"""
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [neighbourhood_risk_history]