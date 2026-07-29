from uuid import uuid4

import pytest
from unittest.mock import Mock

from app.models.detection_event import DetectionType
from app.models.risk_score_history import RiskLevel
from app.services.risk_score_service import calculate_risk_score_handler

class TestRiskScore:
    def setup_method(self):
        self.neighbourhood_id = uuid4()

        self.mock_db = Mock()

        self.mock_rows = [
            (DetectionType.WEAPON_DETECTED, 5),
            (DetectionType.LOITERING, 1),
            (DetectionType.FALL_DETECTED, 3),
        ]


        self.mock_db.execute.return_value.all.side_effect = [self.mock_rows]

        self.mock_threshold = Mock()
        self.mock_threshold.low_max = 30.0
        self.mock_threshold.medium_max = 70.0
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [self.mock_threshold]

        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()


    def reset_side_effects(self, rows=None, threshold=None, default_threshold=None):
        self.mock_db.execute.return_value.all.side_effect = [rows if rows is not None else []]
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [threshold]
        if default_threshold is not None:
            self.mock_db.execute.return_value.scalar_one.side_effect = [default_threshold]

    @pytest.mark.asyncio
    async def test_happy_path(self):
        new_score = calculate_risk_score_handler(self.neighbourhood_id, self.mock_db)

        assert new_score.neighbourhood_id == self.neighbourhood_id
        assert new_score.score == 79
        assert new_score.alert_count == 9
        assert new_score.classification == RiskLevel.HIGH 

        assert self.mock_db.execute.call_count == 2 
        assert self.mock_db.add.call_count == 1
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1
        assert self.mock_db.rollback.call_count == 0


    @pytest.mark.asyncio
    async def test_low_classification(self):
        self.reset_side_effects(
            rows=[(DetectionType.LOITERING, 1)],
            threshold=self.mock_threshold,
        )

        new_score = calculate_risk_score_handler(self.neighbourhood_id, self.mock_db)

        assert new_score.score == 5
        assert new_score.alert_count == 1
        assert new_score.classification == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_critical_override_forces_high(self):
        self.reset_side_effects(
            rows=[(DetectionType.WEAPON_DETECTED, 1)],
            threshold=self.mock_threshold,
        )

        new_score = calculate_risk_score_handler(self.neighbourhood_id, self.mock_db)

        assert new_score.score == 10.0            
        assert new_score.classification == RiskLevel.HIGH

    @pytest.mark.asyncio
    async def test_no_detections(self):
        self.reset_side_effects(rows=[], threshold=self.mock_threshold)

        new_score = calculate_risk_score_handler(self.neighbourhood_id, self.mock_db)

        assert new_score.score == 0
        assert new_score.alert_count == 0
        assert new_score.classification == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_threshold_fallback_to_default(self):
        mock_default_threshold = Mock()
        mock_default_threshold.low_max = 25.0
        mock_default_threshold.medium_max = 60.0

        self.reset_side_effects(
            rows=[(DetectionType.PERIMETER_SCAN, 10)],  # score = 10*4 = 40
            threshold=None,                              # neighbourhood-specific lookup misses
            default_threshold=mock_default_threshold,
        )

        new_score = calculate_risk_score_handler(self.neighbourhood_id, self.mock_db)

        assert new_score.score == 40.0
        assert new_score.classification == RiskLevel.MEDIUM  # 25 < 40 <= 60, using the DEFAULT thresholds

        assert self.mock_db.execute.call_count == 3