from fastapi import HTTPException
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from app.models.risk_score_history import RiskLevel
from app.services.risk_score_history_service import get_neighbourhood_score_handler, get_neighbourhood_score_history_handler

GET_USER_PATCH = "app.services.risk_score_history_service.get_user_by_claims"

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

        self.mock_db.add = Mock()
        self.mock_db.flush = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.user_patcher = patch(GET_USER_PATCH, new=AsyncMock(return_value=self.mock_user))
        self.user_patcher.start()

        self._wire_db(authorised=True, risk_score=self.mock_risk_score)

    def teardown_method(self):
        self.user_patcher.stop()

    def _wire_db(self, authorised: bool, risk_score=None):
        """Rebuilds db.execute with a fresh side_effect list matching the real function's
            call order: [auth check] then, only if authorised, [risk score lookup]"""

        auth_result = Mock()
        auth_result.scalars.return_value.first.return_value = (
            self.mock_neighbourhood if authorised else None
        )

        if not authorised:
            self.mock_db.execute = AsyncMock(side_effect=[auth_result])
            return

        score_result = Mock()
        score_result.scalar_one_or_none.return_value = risk_score

        self.mock_db.execute = AsyncMock(side_effect=[auth_result, score_result])

    # def reset_side_effects(self, neighbourhood_risk_history=None):
    #     """Helper to reset side_effect between tests"""
    #     self.mock_result = Mock()
    #     self.mock_result.scalar_one_or_none.side_effect = [neighbourhood_risk_history]
    #     self.mock_db.execute = AsyncMock(return_value=self.mock_result)

    @pytest.mark.asyncio
    async def test_happy_path(self):
        risk_score = await get_neighbourhood_score_handler(
            self.neighbourhood_id,
            self.mock_db,
            self.mock_claims
        )

        assert risk_score.neighbourhood_id == self.neighbourhood_id
        assert risk_score.alert_count == 19
        assert risk_score.classification == RiskLevel.HIGH
        assert risk_score.score == 214

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_not_authorised(self):
        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        with pytest.raises(HTTPException) as exception:
            await get_neighbourhood_score_handler(
                wrong_neighbourhood_id,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403
        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_risk_not_found(self):
        self.reset_side_effects(neighbourhood_risk_history=None)

        with pytest.raises(HTTPException) as exception:
            await get_neighbourhood_score_handler(
                self.neighbourhood_id,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 404

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0


class TestGetNeighbourhoodScoreHistory:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.add = Mock()
        self.mock_db.flush = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id": str(self.neighbourhood_id)}

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.user_patcher = patch(GET_USER_PATCH, new=AsyncMock(return_value=self.mock_user))
        self.user_patcher.start()

        self.mock_neighbourhood = Mock()

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

        # default wiring: authorised, history rows present
        self._wire_db(authorised=True, history_rows=self.mock_list)

    def teardown_method(self):
        self.user_patcher.stop()

    def _wire_db(self, authorised: bool, history_rows=None):
        """Rebuilds db.execute matching the real call order:
        [auth check] then, only if authorised AND granularity is valid,
        [history query]. Since the granularity check happens between the
        two queries with no DB call of its own, tests that only need the
        auth check to pass (e.g. invalid granularity) still get a second
        item queued — it's just never consumed if the function raises
        before reaching it."""
        auth_result = Mock()
        auth_result.scalars.return_value.first.return_value = (
            self.mock_neighbourhood if authorised else None
        )

        if not authorised:
            self.mock_db.execute = AsyncMock(side_effect=[auth_result])
            return

        history_result = Mock()
        history_result.all.return_value = history_rows if history_rows is not None else []

        self.mock_db.execute = AsyncMock(side_effect=[auth_result, history_result])

    @pytest.mark.asyncio
    async def test_happy_path(self):
        history = await get_neighbourhood_score_history_handler(
            self.neighbourhood_id,
            "day",
            self.mock_db,
            self.mock_claims
        )

        assert len(history) == 3

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_not_authorised(self):
        self._wire_db(authorised=False)
        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        with pytest.raises(HTTPException) as exception:
            await get_neighbourhood_score_history_handler(
                wrong_neighbourhood_id,
                "day",
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403
        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_invalid_granularity(self):
        # auth check must pass for the function to even reach the
        # granularity validation — default setup_method wiring already
        # has authorised=True, so no re-wiring needed here.
        with pytest.raises(HTTPException) as exception:
            await get_neighbourhood_score_history_handler(
                self.neighbourhood_id,
                "mock_wrong",
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 400
        # only the auth check ran — granularity check fails before the
        # history query is ever built
        assert self.mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_history_not_found(self):
        self._wire_db(authorised=True, history_rows=[])

        with pytest.raises(HTTPException) as exception:
            await get_neighbourhood_score_history_handler(
                self.neighbourhood_id,
                "day",
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 404
        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0