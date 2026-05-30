import pytest
from unittest.mock import patch, Mock

@pytest.mark.asyncio
async def test_stream_health_available(async_client):
    with patch("app.api.controllers.stream.cv2") as mock_cv2:
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.grab.return_value = True
        mock_cv2.VideoCapture.return_value = mock_cap

        r = await async_client.get("/stream/health", params={"url": "rtsp://example"})
        assert r.status_code == 200
        assert r.json()["available"] is True
