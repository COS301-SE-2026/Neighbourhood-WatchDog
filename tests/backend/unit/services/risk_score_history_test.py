from fastapi import HTTPException
import pytest
from unittest.mock import Mock
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from app.models.risk_score_history import RiskLevel
from app.services.risk_score_history_service import get_neighbourhood_score_handler, get_neighbourhood_score_history_handler

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

    @pytest.mark.asyncio
    async def test_not_authorised(self):
        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        with pytest.raises(HTTPException) as exception:
            get_neighbourhood_score_handler(
                wrong_neighbourhood_id,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403
        assert self.mock_db.execute.call_count == 0
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_risk_not_found(self):
        self.reset_side_effects(neighbourhood_risk_history=None)

        with pytest.raises(HTTPException) as exception:
            get_neighbourhood_score_handler(
                self.neighbourhood_id,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 404

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0


class TestGetNeighbourhoodScoreHistory:
    def setup_method(self):
        self.mock_db = Mock()
        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id" : str(self.neighbourhood_id)}

        self.mock_risk_score1 = Mock()
        self.mock_risk_score1.id = uuid4()
        self.mock_risk_score1.neighbourhood_id = self.neighbourhood_id
        self.mock_risk_score1.score = 214
        self.mock_risk_score1.classification = RiskLevel.HIGH
        self.mock_risk_score1.alert_count = 19
        self.mock_risk_score1.calculated_at = datetime.now()

        self.mock_risk_score2 = Mock()
        self.mock_risk_score2.id = uuid4()
        self.mock_risk_score2.neighbourhood_id = self.neighbourhood_id
        self.mock_risk_score2.score = 12
        self.mock_risk_score2.classification = RiskLevel.LOW
        self.mock_risk_score2.alert_count = 5
        self.mock_risk_score2.calculated_at = datetime.now()

        self.mock_risk_score3 = Mock()
        self.mock_risk_score3.id = uuid4()
        self.mock_risk_score3.neighbourhood_id = self.neighbourhood_id
        self.mock_risk_score3.score = 98
        self.mock_risk_score3.classification = RiskLevel.MEDIUM
        self.mock_risk_score3.alert_count = 12
        self.mock_risk_score3.calculated_at = datetime.now()

        self.mock_list = [self.mock_risk_score1, self.mock_risk_score2, self.mock_risk_score3]

        self.mock_db.execute.return_value.all.side_effect = [self.mock_list]


        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

    def reset_side_effects(self, history_list=None):
        self.mock_db.execute.return_value.all.side_effect = [history_list]

    @pytest.mark.asyncio
    async def test_happy_path(self):
        history = get_neighbourhood_score_history_handler(
            self.neighbourhood_id,
            "day",
            self.mock_db,
            self.mock_claims
        )

        assert len(history) == 3


        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_not_authorised(self):
        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        with pytest.raises(HTTPException) as exception:
            get_neighbourhood_score_history_handler(
                wrong_neighbourhood_id,
                "day",
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403
        assert self.mock_db.execute.call_count == 0
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_invalid_granularity(self):
        with pytest.raises(HTTPException) as exception:
            get_neighbourhood_score_history_handler(
                self.neighbourhood_id,
                "mock_wrong",
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 400
        assert self.mock_db.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_history_not_found(self):
        self.reset_side_effects(history_list=[])
        with pytest.raises(HTTPException) as exception:
            get_neighbourhood_score_history_handler(
                self.neighbourhood_id,
                "day",
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 404

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
