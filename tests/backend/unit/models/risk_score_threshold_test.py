from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime
from app.schemas.risk_threshold_config import NeighbourhoodRiskThresholdConfigRes, RiskThresholdConfigRes


def _risk_threshold_res(**overrides):
    base = {
        "id": uuid4(),
        "neighbourhood_id": uuid4(),
        "low_max": float(),
        "medium_max": float(),
        "updated_at": datetime(),
    }
    base.update(overrides)
    return base

class TestRiskThresholdConfigRes:
    def test_valid_fields(self):
        "Happy path: all required fields"
        data = _risk_threshold_res()
        res = RiskThresholdConfigRes(**data)

        assert res.id == data["id"]
        assert res.neighbourhood_id == data["neighbourhood_id"]
        assert res.low_max == data["low_max"]
        assert res.medium_max == data["medium_max"]
        assert res.updated_at == data["updated_at"]

    def test_missing_id_raises_validation_error(self):
            data = _risk_threshold_res()
            del data["id"]
    
            with pytest.raises(ValidationError):
                RiskThresholdConfigRes(**data)

    def test_missing_low_max_raises_validation_error(self):
            data = _risk_threshold_res()
            del data["low_max"]
    
            with pytest.raises(ValidationError):
                RiskThresholdConfigRes(**data)

    def test_missing_medium_max_raises_validation_error(self):
            data = _risk_threshold_res()
            del data["medium_max"]
    
            with pytest.raises(ValidationError):
                RiskThresholdConfigRes(**data)

    def test_missing_updated_at_raises_validation_error(self):
            data = _risk_threshold_res()
            del data["updated_at"]
    
            with pytest.raises(ValidationError):
                RiskThresholdConfigRes(**data)

    def test_missing_neighbourhood_id_does_not_raise(self):
            data = _risk_threshold_res()
            data["neighbourhood_id"] == None

            assert data["neighbourhood_id"] is None
    
    def test_from_attributes_config_present(self):
        """model_config should allow construction from ORM objects"""
        assert RiskThresholdConfigRes.model_config.get("from_attributes") is True
