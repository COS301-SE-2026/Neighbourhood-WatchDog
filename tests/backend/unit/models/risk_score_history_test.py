from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.models.risk_score_history import RiskLevel
from app.schemas.risk_score_history import RiskScoreRes ,NeighbourhoodRiskScoreRes, NeighbourhoodRiskScoreHistoryRes


def _risk_score_res(**overrides):
    base = {
        "neighbourhood_id": uuid4(),
        "score": float(),
        "classification": RiskLevel.MEDIUM,
        "alert_count": int(),
        "calculated_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base

class TestRiskScoreRes:
    def test_valid_fields(self):
        """Happy path: all required fields"""
        data = _risk_score_res()
        res = RiskScoreRes(**data)
    
        assert res.neighbourhood_id == data["neighbourhood_id"]
        assert res.score == data["score"]
        assert res.classification == RiskLevel.MEDIUM
        assert res.alert_count == data["alert_count"]
        assert res.calculated_at == data["calculated_at"]

    def test_missing_neighbourhood_id_raises_validation_error(self):
        data = _risk_score_res()
        del data["neighbourhood_id"]

        with pytest.raises(ValidationError):
            RiskScoreRes(**data)

    def test_missing_score_raises_validation_error(self):
        data = _risk_score_res()
        del data["score"]

        with pytest.raises(ValidationError):
            RiskScoreRes(**data)

    def test_missing_classification_raises_validation_error(self):
        data = _risk_score_res()
        del data["classification"]

        with pytest.raises(ValidationError):
            RiskScoreRes(**data)

    def test_invalid_classification_raises_validation_error(self):
        with pytest.raises(ValidationError):
            RiskScoreRes(**_risk_score_res(classification="INVALID"))

    def test_missing_alert_count_raises_validation_error(self):
        data = _risk_score_res()
        del data["alert_count"]

        with pytest.raises(ValidationError):
            RiskScoreRes(**data)

    def test_missing_calculated_at_raises_validation_error(self):
        data = _risk_score_res()
        del data["calculated_at"]

        with pytest.raises(ValidationError):
            RiskScoreRes(**data)

    def test_invalid_uuid_for_neighbourhood_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            RiskScoreRes(**_risk_score_res(neighbourhood_id="invalid-uuid"))

    def test_from_attributes_config_present(self):
            """model_config should allow construction from ORM objects"""
            assert RiskScoreRes.model_config.get("from_attributes") is True

