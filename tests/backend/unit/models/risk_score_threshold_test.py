from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.schemas.risk_threshold_config import NeighbourhoodRiskThresholdConfigRes, RiskThresholdConfigRes


def _risk_threshold_res(**overrides):
    base = {
        "id": uuid4(),
        "neighbourhood_id": uuid4(),
        "low_max": float(),
        "medium_max": float(),
        "updated_at": datetime.now(timezone.utc),
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
            data = _risk_threshold_res(neighbourhood_id=None)
            res = RiskThresholdConfigRes(**data)

            assert res.neighbourhood_id is None
    
    def test_from_attributes_config_present(self):
        """model_config should allow construction from ORM objects"""
        assert RiskThresholdConfigRes.model_config.get("from_attributes") is True

class TestNeighbourhoodRiskThresholdConfigRes:
    def _make_nested_res(self) -> RiskThresholdConfigRes:
         return RiskThresholdConfigRes(**_risk_threshold_res())

    def test_valid_response_with_data(self):
        """Happy path, all fields present"""
        nested = self._make_nested_res()
        res = NeighbourhoodRiskThresholdConfigRes(
             status=200,
             message="Neighbourhood risk threshold retrieved successfully",
             data=nested,
        )

        assert res.status == 200
        assert res.message == "Neighbourhood risk threshold retrieved successfully"
        assert res.data is not None

    def test_missing_status_raises_validation_error(self):
        with pytest.raises(ValidationError):
            NeighbourhoodRiskThresholdConfigRes(
                message="Neighbourhood risk threshold retrieved successfully", data=self._make_nested_res(),)

    def test_missing_data_raises_validation_error(self):
            with pytest.raises(ValidationError):
                NeighbourhoodRiskThresholdConfigRes(status=200, message="Neighbourhood risk threshold retrieved successfully")

    def test_missing_message_raises_validation_error(self):
            with pytest.raises(ValidationError):
                NeighbourhoodRiskThresholdConfigRes(status=200, data=self._make_nested_res(),) 

    def test_invalid_nested_data_raises_validation_error(self):
         with pytest.raises(ValidationError):
            NeighbourhoodRiskThresholdConfigRes(status=200, data={"low_max": "not-a-float"})
         