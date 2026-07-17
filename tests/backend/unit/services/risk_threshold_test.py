from datetime import datetime
from uuid import UUID, uuid4

import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from app.services.risk_threshold_config_service import get_neighbourhood_risk_threshold_handler, update_neighbourhood_risk_threshold_handler
from app.schemas.risk_threshold_config import RiskThresholdConfigRes, UpdateRiskThresholdConfigReq, NeighbourhoodRiskThresholdConfigRes

class TestGetRiskThresholdConfig:
    def setup_method(self):
        self.mock_db = Mock()
        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id" : str(self.neighbourhood_id)}

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


        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_risk_threshold_config,
        ]

        self.mock_db.execute.return_value.scalar_one.side_effect = []

        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

    def reset_side_effects(self, neighbourhood_threshold_config=None, global_default_config=None):
        """Helper to reset side_effect between tests"""
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            neighbourhood_threshold_config
        ]
        if global_default_config is not None:
            self.mock_db.execute.return_value.scalar_one.side_effect = [global_default_config]

    @pytest.mark.asyncio
    async def test_happy_path_get(self):
        """
            Neighbourhood admin successfuly gets theshold config
        """

        neighbourhood_risk_config = get_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id, 
            self.mock_db, 
            self.mock_claims
        )

        assert self.mock_db.execute.call_count == 1
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

        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        

        with pytest.raises(HTTPException) as exception:
            get_neighbourhood_risk_threshold_handler(
                wrong_neighbourhood_id,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403

        assert self.mock_db.execute.call_count == 0
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_no_neighbourhood_config(self):
        self.reset_side_effects(
            neighbourhood_threshold_config=None, 
            global_default_config=self.mock_default_threshold_config
        )

        neighbourhood_risk_config = get_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id, 
            self.mock_db, 
            self.mock_claims
        )

        assert self.mock_db.execute.call_count == 2
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
        self.neighbourhood_id = uuid4()
        self.mock_claims = {"custom:neighbourhood_id" : str(self.neighbourhood_id)}

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

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_risk_threshold_config,
        ]

        self.mock_db.execute.return_value.scalar_one.side_effect = []

        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

    def reset_side_effects(self, neighbourhood_threshold_config=None, global_default_config=None):
        """Helper to reset side_effect between tests"""
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            neighbourhood_threshold_config
        ]
        if global_default_config is not None:
            self.mock_db.execute.return_value.scalar_one.side_effect = [global_default_config]
        
    @pytest.mark.asyncio
    async def test_happy_path_update(self):
        
        req = UpdateRiskThresholdConfigReq(
            low_max=45.2,
            medium_max=90.1
        )

        updated_risk_threshold_config = update_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id,
            req,
            self.mock_db,
            self.mock_claims
        )

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1

        assert updated_risk_threshold_config.low_max == 45.2
        assert updated_risk_threshold_config.medium_max == 90.1
        assert updated_risk_threshold_config.neighbourhood_id == self.neighbourhood_id

    @pytest.mark.asyncio
    async def test_not_authorised(self):
        """Not authorised for this neighbourhood"""

        wrong_neighbourhood_id = UUID("717159e3-2ea3-4163-9773-e908fec43be6")

        req = UpdateRiskThresholdConfigReq(
            low_max=45.2,
            medium_max=90.1
        )

        with pytest.raises(HTTPException) as exception:
            update_neighbourhood_risk_threshold_handler(
                wrong_neighbourhood_id,
                req,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 403

        assert self.mock_db.execute.call_count == 0
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_req(self):
        with pytest.raises(ValueError) as ve:
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

        with pytest.raises(HTTPException) as exception:
            update_neighbourhood_risk_threshold_handler(
                self.neighbourhood_id,
                req,
                self.mock_db,
                self.mock_claims
            )

        assert self.mock_db.execute.call_count == 1
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

        self.mock_db.refresh.side_effect = fake_refresh

        self.reset_side_effects(
            neighbourhood_threshold_config=None, 
            global_default_config=self.mock_default_threshold_config
        )

        req = UpdateRiskThresholdConfigReq(low_max=28)

        updated_risk_threshold_config = update_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id,
            req,
            self.mock_db,
            self.mock_claims
        )

        assert updated_risk_threshold_config.neighbourhood_id == self.neighbourhood_id
        assert updated_risk_threshold_config.low_max == 28
        assert updated_risk_threshold_config.medium_max == 70
        assert updated_risk_threshold_config.id != self.mock_default_threshold_config.id

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.add.call_count == 1
        assert self.mock_db.rollback.call_count == 0
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1

    @pytest.mark.asyncio
    async def test_partial_update_existing_config(self):
        """Existing neighbourhood-specific config, PATCH only one field, other field untoched"""
        req = UpdateRiskThresholdConfigReq(medium_max=60)

        updated_config = update_neighbourhood_risk_threshold_handler(
            self.neighbourhood_id,
            req,
            self.mock_db,
            self.mock_claims
        )

        assert updated_config.low_max == 20
        assert updated_config.medium_max == 60

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.add.call_count == 0
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.refresh.call_count == 1

    @pytest.mark.asyncio
    async def test_partial_update_invalid_state(self):
        """send one invalid field and combine it with existing config"""
        req = UpdateRiskThresholdConfigReq(medium_max=15)

        with pytest.raises(HTTPException) as exception:
            update_neighbourhood_risk_threshold_handler(
                self.neighbourhood_id,
                req,
                self.mock_db,
                self.mock_claims
            )

        assert exception.value.status_code == 422

        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.dd.call_count == 0
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.refresh.call_count == 0
        assert self.mock_db.rollback.call_count == 0
