from datetime import datetime
from uuid import UUID, uuid4

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from app.services.risk_threshold_config_service import get_neighbourhood_risk_threshold_handler, update_neighbourhood_risk_threshold_handler
from app.schemas.risk_threshold_config import UpdateRiskThresholdConfigReq

GET_USER_PATCH = "app.services.risk_threshold_config_service.get_user_by_claims"

class TestGetRiskThresholdConfig:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.add = Mock()
        self.mock_db.flush = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id" : str(self.neighbourhood_id)}

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.user_patcher = patch(GET_USER_PATCH, new=AsyncMock(return_value=self.mock_user))
        self.user_patcher.start()

        self.mock_neighbourhood = Mock()

        self.mock_risk_threshold_config = Mock()
        self.mock_risk_threshold_config.id = uuid4()
        self.mock_risk_threshold_config.neighbourhood_id = self.neighbourhood_id
        self.mock_risk_threshold_config.low_max = 20
        self.mock_risk_threshold_config.medium_max = 50
        self.mock_risk_threshold_config.updated_at = datetime.now()

        self.mock_default_threshold_config = Mock()
        self.mock_default_threshold_config.id = uuid4()
        self.mock_default_threshold_config.neighbourhood_id = None
        self.mock_default_threshold_config.low_max = 30
        self.mock_default_threshold_config.medium_max = 70
        self.mock_default_threshold_config.updated_at = datetime.now()

        self._wire_db(authorised=True, config=self.mock_risk_threshold_config)
    
    def teardown_method(self):
        self.user_patcher.stop()

    def _wire_db(self, authorised: bool, config=None, default_config=None):
        """Rebuilds db.execute with a fresh side_effect list matching the real function's
            call order: 
            [auth check] 
            then [config lookup]
            then default lookup """

        auth_result = Mock()
        auth_result.scalars.return_value.first.return_value = (
            self.mock_neighbourhood if authorised else None
        )

        if not authorised:
            self.mock_db.execute = AsyncMock(side_effect=[auth_result])
            return

        config_result = Mock()
        config_result.scalars.return_value.first.return_value = config

        side_effects = [auth_result, config_result]

        if config is None and default_config is not None:
            default_result = Mock()
            default_result.scalars.return_value.first.return_value = default_config
            side_effects.append(default_result)

        self.mock_db.execute = AsyncMock(side_effect=side_effects)

    @pytest.mark.asyncio
    async def test_happy_path_get(self):
        """
            Neighbourhood admin successfuly gets theshold config
        """

        neighbourhood_risk_config = await get_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id, 
            self.mock_db, 
            self.mock_claims
        )

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0

        assert neighbourhood_risk_config is not None
        assert neighbourhood_risk_config.neighbourhood_id == self.neighbourhood_id
        assert neighbourhood_risk_config.low_max == 20
        assert neighbourhood_risk_config.medium_max == 50
        assert neighbourhood_risk_config.updated_at == self.mock_risk_threshold_config.updated_at

    @pytest.mark.asyncio
    async def test_not_authorised(self):
        """Not authorised for this neighbourhood"""
        self._wire_db(authorised=False)

        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        with pytest.raises(HTTPException) as exception:
            await get_neighbourhood_risk_threshold_handler(
                wrong_neighbourhood_id,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_no_neighbourhood_config(self):
        self._wire_db(authorised=True, config=None, default_config=self.mock_default_threshold_config)


        neighbourhood_risk_config = await get_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id, 
            self.mock_db, 
            self.mock_claims
        )

        assert self.mock_db.execute.call_count == 3
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0

        assert neighbourhood_risk_config is not None
        assert neighbourhood_risk_config.neighbourhood_id is None
        assert neighbourhood_risk_config.low_max == 30
        assert neighbourhood_risk_config.medium_max == 70
        assert neighbourhood_risk_config.updated_at == self.mock_default_threshold_config.updated_at

class TestUpdateRiskThresholdConfig:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.add = Mock()
        self.mock_db.flush = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id" : str(self.neighbourhood_id)}

        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.user_patcher = patch(GET_USER_PATCH, new=AsyncMock(return_value=self.mock_user))
        self.user_patcher.start()

        self.mock_neighbourhood = Mock()

        self.mock_risk_threshold_config = Mock()
        self.mock_risk_threshold_config.id = uuid4()
        self.mock_risk_threshold_config.neighbourhood_id = self.neighbourhood_id
        self.mock_risk_threshold_config.low_max = 20
        self.mock_risk_threshold_config.medium_max = 50
        self.mock_risk_threshold_config.updated_at = datetime.now()

        self.mock_default_threshold_config = Mock()
        self.mock_default_threshold_config.id = uuid4()
        self.mock_default_threshold_config.neighbourhood_id = None
        self.mock_default_threshold_config.low_max = 30
        self.mock_default_threshold_config.medium_max = 70
        self.mock_default_threshold_config.updated_at = datetime.now()

        self._wire_db(authorised=True, config=self.mock_risk_threshold_config)
            
    def teardown_method(self):
        self.user_patcher.stop()

    def _wire_db(self, authorised: bool, config=None, default_config=None):
        auth_result = Mock()
        auth_result.scalars.return_value.first.return_value = (
            self.mock_neighbourhood if authorised else None
        )

        if not authorised:
            self.mock_db.execute = AsyncMock(side_effect=[auth_result])
            return

        config_result = Mock()
        config_result.scalars.return_value.first.return_value = config

        side_effects = [auth_result, config_result]

        if config is None and default_config is not None:
            default_result = Mock()
            default_result.scalars.return_value.first.return_value = default_config
            side_effects.append(default_result)

        self.mock_db.execute = AsyncMock(side_effect=side_effects)

    @pytest.mark.asyncio
    async def test_happy_path_update(self):
        
        req = UpdateRiskThresholdConfigReq(
            low_max=45.2,
            medium_max=90.1
        )

        updated_risk_threshold_config = await update_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id,
            req,
            self.mock_db,
            self.mock_claims
        )

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1

        assert updated_risk_threshold_config.low_max == 45.2
        assert updated_risk_threshold_config.medium_max == 90.1
        assert updated_risk_threshold_config.neighbourhood_id == self.neighbourhood_id

    @pytest.mark.asyncio
    async def test_not_authorised(self):
        self._wire_db(authorised=False)
        """Not authorised for this neighbourhood"""

        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        req = UpdateRiskThresholdConfigReq(
            low_max=45.2,
            medium_max=90.1
        )

        with pytest.raises(HTTPException) as exception:
            await update_neighbourhood_risk_threshold_handler(
                wrong_neighbourhood_id,
                req,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_req(self):
        with pytest.raises(ValueError):
            UpdateRiskThresholdConfigReq(
                low_max=None,
                medium_max=None
            )

        assert self.mock_db.execute.call_count == 0
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_incorrect_threshold(self):
        """Testing with low threshold higher than medium"""
        req = UpdateRiskThresholdConfigReq(
            low_max=100.2,
            medium_max=70.1
        )

        with pytest.raises(HTTPException):
            await update_neighbourhood_risk_threshold_handler(
                self.neighbourhood_id,
                req,
                self.mock_db,
                self.mock_claims
            )

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0

    @pytest.mark.asyncio
    async def test_update_default(self):
        def fake_refresh(obj):
            if obj.id is None:
                obj.id = uuid4()
            if obj.updated_at is None:
                obj.updated_at = datetime.now()

        self.mock_db.refresh.side_effect = AsyncMock(side_effect=fake_refresh)

        self._wire_db(authorised=True, config=None, default_config=self.mock_default_threshold_config)

        req = UpdateRiskThresholdConfigReq(low_max=28)

        updated_risk_threshold_config = await update_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id,
            req,
            self.mock_db,
            self.mock_claims
        )

        assert updated_risk_threshold_config.neighbourhood_id == self.neighbourhood_id
        assert updated_risk_threshold_config.low_max == 28
        assert updated_risk_threshold_config.medium_max == 70
        assert updated_risk_threshold_config.id != self.mock_default_threshold_config.id

        assert self.mock_db.execute.call_count == 3
        assert self.mock_db.add.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1

    @pytest.mark.asyncio
    async def test_partial_update_existing_config(self):
        """Existing neighbourhood-specific config, PATCH only one field, other field untoched"""
        req = UpdateRiskThresholdConfigReq(medium_max=60)

        updated_config = await update_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id,
            req,
            self.mock_db,
            self.mock_claims
        )

        assert updated_config.low_max == 20
        assert updated_config.medium_max == 60

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1

    @pytest.mark.asyncio
    async def test_partial_update_invalid_state(self):
        """send one invalid field and combine it with existing config"""
        req = UpdateRiskThresholdConfigReq(medium_max=15)

        with pytest.raises(HTTPException) as exception:
            await update_neighbourhood_risk_threshold_handler(
                self.neighbourhood_id,
                req,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 422

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0
