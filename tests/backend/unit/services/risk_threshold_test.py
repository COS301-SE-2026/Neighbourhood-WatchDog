from datetime import datetime
from uuid import UUID, uuid4

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.services.risk_threshold_config_service import get_neighbourhood_risk_threshold_handler, update_neighbourhood_risk_threshold_handler
from app.schemas.risk_threshold_config import RiskThresholdConfigRes, UpdateRiskThresholdConfigReq, NeighbourhoodRiskThresholdConfigRes

class TestRiskThresholdConfig:
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
    async def test_happy_path(self):
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