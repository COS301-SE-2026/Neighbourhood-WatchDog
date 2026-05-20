import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.models.alert import Alert
from app.models.detection_event import DetectionEvent
from app.models.camera import Camera
from app.models.zone import GeospatialZone
from app.schemas.detection import DetectionIngestReq
from app.services.detection_service import ingest_detection_handler


class TestIngestDetection:
    def setup_method(self):
        self.mock_db = Mock()
        self.mock_db.execute = Mock()
        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.rollback = Mock()
        self.claims = {"sub": "system"}

        self._added = []

        def _ensure_defaults(obj):
            if hasattr(obj, "id") and getattr(obj, "id") is None:
                obj.id = uuid.uuid4()
            if hasattr(obj, "created_at") and getattr(obj, "created_at") is None:
                obj.created_at = datetime.now(timezone.utc)

        def _add(obj):
            self._added.append(obj)

        def _flush():
            if self._added:
                _ensure_defaults(self._added[-1])

        def _refresh(obj):
            _ensure_defaults(obj)

        self.mock_db.add.side_effect = _add
        self.mock_db.flush.side_effect = _flush
        self.mock_db.refresh.side_effect = _refresh

        self.alert_patcher = patch("app.services.detection_service.Alert", new=Alert)
        self.event_patcher = patch("app.services.detection_service.DetectionEvent", new=DetectionEvent)
        self.camera_patcher = patch("app.services.detection_service.Camera", new=Camera)
        self.zone_patcher = patch("app.services.detection_service.GeospatialZone", new=GeospatialZone)

        self.alert_patcher.start()
        self.event_patcher.start()
        self.camera_patcher.start()
        self.zone_patcher.start()

    def teardown_method(self):
        self.alert_patcher.stop()
        self.event_patcher.stop()
        self.camera_patcher.stop()
        self.zone_patcher.stop()

    def _make_request(self, confidence: float, zone_id: uuid.UUID | None = None) -> DetectionIngestReq:
        return DetectionIngestReq(
            camera_id=uuid.uuid4(),
            frame_timestamp=datetime.now(timezone.utc),
            detection_type="HUMAN_PRESENCE",
            confidence_score=confidence,
            zone_id=zone_id,
        )

    @pytest.mark.asyncio
    async def test_above_threshold_creates_alert(self):
        data = self._make_request(0.9)
        camera = Mock()
        camera.neighbourhood_id = uuid.uuid4()
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = camera

        with patch("app.api.controllers.alert.broadcast", new_callable=AsyncMock) as mock_broadcast:
            result = await ingest_detection_handler(data, self.mock_db, self.claims)

        assert result.alert_created is True
        assert result.alert_id is not None
        assert result.data.processed is True
        assert self.mock_db.add.call_count == 2
        assert self.mock_db.commit.call_count == 1
        assert mock_broadcast.call_count == 1

    @pytest.mark.asyncio
    async def test_below_threshold_does_not_create_alert(self):
        data = self._make_request(0.1)
        result = await ingest_detection_handler(data, self.mock_db, self.claims)

        assert result.alert_created is False
        assert result.alert_id is None
        assert result.data.processed is True
        assert self.mock_db.add.call_count == 1
        assert self.mock_db.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_invalid_detection_type_raises_400(self):
        data = Mock()
        data.camera_id = uuid.uuid4()
        data.frame_timestamp = datetime.now(timezone.utc)
        data.detection_type = "ALIEN"
        data.confidence_score = 0.5
        data.thumbnail_url = None
        data.zone_id = None

        with pytest.raises(HTTPException) as exc:
            await ingest_detection_handler(data, self.mock_db, self.claims)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_confidence_out_of_range_raises_400(self):
        data = Mock()
        data.camera_id = uuid.uuid4()
        data.frame_timestamp = datetime.now(timezone.utc)
        data.detection_type = "HUMAN_PRESENCE"
        data.confidence_score = 2.5
        data.thumbnail_url = None
        data.zone_id = None

        with pytest.raises(HTTPException) as exc:
            await ingest_detection_handler(data, self.mock_db, self.claims)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_detection_event_always_stored(self):
        data = self._make_request(0.1)
        await ingest_detection_handler(data, self.mock_db, self.claims)

        assert self.mock_db.add.call_count == 1
        assert self.mock_db.commit.call_count == 1
