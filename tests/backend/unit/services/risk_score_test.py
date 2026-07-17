from uuid import uuid4

import pytest
from unittest.mock import Mock, patch

from app.models.detection_event import DetectionType
from app.services.risk_score_service import CRITICAL_DETECTION_TYPES, SEVERITY_WEIGHTS

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