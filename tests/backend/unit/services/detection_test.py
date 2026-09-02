import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from pydantic import ValidationError
import pytest
from fastapi import HTTPException

from app.models.camera import Camera
from app.schemas.detection import DetectionIngestReq
from app.services.detection_service import ingest_detection_handler


class TestIngestDetection:
    def setup_method(self):
        self.mock_db = Mock()

        # AsyncSession methods that your service awaits.
        self.mock_db.execute = AsyncMock()
        self.mock_db.flush = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.rollback = AsyncMock()

        # AsyncSession.add() is synchronous.
        self.mock_db.add = Mock()

        self.claims = {"sub": "system"}
        self.added_objects = []

        def capture_added_object(obj):
            self.added_objects.append(obj)

        async def assign_alert_defaults():
            if not self.added_objects:
                return

            alert = self.added_objects[-1]

            if alert.id is None:
                alert.id = uuid.uuid4()

            if alert.created_at is None:
                alert.created_at = datetime.now(timezone.utc)

        self.mock_db.add.side_effect = capture_added_object
        self.mock_db.flush.side_effect = assign_alert_defaults

    def make_request(self, confidence: float) -> DetectionIngestReq:
        return DetectionIngestReq(
            camera_id=uuid.uuid4(),
            frame_timestamp=datetime.now(timezone.utc),
            detection_type="HUMAN_PRESENCE",
            confidence_score=confidence,
            zone_id=None,
            thumbnail_url=None,
        )

    @pytest.mark.asyncio
    async def test_above_threshold_creates_alert_and_notifies_users(self):
        data = self.make_request(confidence=0.90)

        camera = Mock(spec=Camera)
        camera.property_id = uuid.uuid4()
        camera.name = "Front Gate Camera"
        camera.location = "Main Entrance"

        camera_result = Mock()
        camera_result.scalar_one_or_none.return_value = camera

        recipients_result = Mock()
        recipients_result.scalars.return_value.all.return_value = [
            uuid.uuid4(),
            uuid.uuid4(),
        ]

        self.mock_db.execute.side_effect = [
            camera_result,
            recipients_result,
        ]

        with (
            patch(
                "app.api.controllers.alert.broadcast",
                new_callable=AsyncMock,
            ) as mock_broadcast,
            patch(
                "app.services.detection_service.dispatch_notifications",
                new_callable=AsyncMock,
            ) as mock_dispatch,
        ):
            result = await ingest_detection_handler(
                data,
                self.mock_db,
                self.claims,
            )

        assert result.status == 201
        assert result.alert_created is True
        assert result.alert_id is not None

        # Only the merged Alert is persisted.
        assert self.mock_db.add.call_count == 1
        assert self.mock_db.commit.call_count == 1

        mock_broadcast.assert_awaited_once()
        mock_dispatch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_below_threshold_creates_no_alert(self):
        data = self.make_request(confidence=0.10)

        result = await ingest_detection_handler(
            data,
            self.mock_db,
            self.claims,
        )

        assert result.status == 201
        assert result.alert_created is False
        assert result.alert_id is None

        # Below threshold: no Alert and no DetectionEvent are persisted.
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_awaited_once()
        self.mock_db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_invalid_detection_type_raises_400(self):
        data = self.make_request(confidence=0.50)
        data.detection_type = "ALIEN"

        with pytest.raises(HTTPException) as exc:
            await ingest_detection_handler(data, self.mock_db, self.claims)

        assert exc.value.status_code == 400
        assert exc.value.detail == "Invalid detection type"

    def test_confidence_above_one_is_rejected_by_request_schema(self):
        with pytest.raises(ValidationError) as exc:
            self.make_request(confidence=1.10)

        assert "confidence_score must be between 0 and 1" in str(exc.value)