import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
import main as m

from app.core.database import get_db

ALERT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
CAMERA_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
NEIGHBOURHOOD_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
 
def _make_alert():
    alert = Mock()
    alert.id = ALERT_ID
    alert.camera_id = CAMERA_ID
    return alert
 
def _make_camera(neighbourhood_id=NEIGHBOURHOOD_ID):
    camera = Mock()
    camera.id = CAMERA_ID
    camera.neighbourhood_id = neighbourhood_id
    return camera
 
def _make_notification(channel="WHATSAPP", status="SENT"):
    n = Mock()
    n.id = uuid.uuid4()
    n.alert_id = ALERT_ID
    n.user_id = uuid.uuid4()
    n.channel = channel
    n.status = status
    n.sent_at = datetime.now(timezone.utc)
    return n
 
def _make_mock_db(alert=None, camera=None, notifications=None):
    mock_db = Mock()
    scalar_results = iter([alert, camera])
 
    def _execute(*args, **kwargs):
        result = Mock()
        try:
            result.scalar_one_or_none.return_value = next(scalar_results)
        except StopIteration:
            result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = notifications or []
        return result
 
    mock_db.execute.side_effect = _execute
    return mock_db
 
def _headers_for_neighbourhood(headers: dict, neighbourhood_id=NEIGHBOURHOOD_ID) -> dict:
    return {**headers, "X-Mock-Neighbourhood-Id": str(neighbourhood_id)}
 
class TestListNotificationsForAlert:
    def teardown_method(self):
        m.app.dependency_overrides.pop(get_db, None)
 
    @pytest.mark.asyncio
    async def test_admin_can_list_notifications(self, async_client, admin_headers):
        alert = _make_alert()
        camera = _make_camera(neighbourhood_id=NEIGHBOURHOOD_ID)
        notifications = [_make_notification()]
        mock_db = _make_mock_db(alert=alert, camera=camera, notifications=notifications)
        m.app.dependency_overrides[get_db] = lambda: mock_db
 
        headers = _headers_for_neighbourhood(admin_headers)
        response = await async_client.get(f"/notifications/{ALERT_ID}", headers=headers)
 
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == 200
        assert len(body["data"]) == 1
        assert body["data"][0]["channel"] == "WHATSAPP"
 
    @pytest.mark.asyncio
    async def test_empty_notifications_returns_empty_list(self, async_client, admin_headers):
        alert = _make_alert()
        camera = _make_camera(neighbourhood_id=NEIGHBOURHOOD_ID)
        mock_db = _make_mock_db(alert=alert, camera=camera, notifications=[])
        m.app.dependency_overrides[get_db] = lambda: mock_db
 
        headers = _headers_for_neighbourhood(admin_headers)
        response = await async_client.get(f"/notifications/{ALERT_ID}", headers=headers)
 
        assert response.status_code == 200
        assert response.json()["data"] == []
 
    @pytest.mark.asyncio
    async def test_resident_role_forbidden(self, async_client, auth_headers):
        mock_db = _make_mock_db()
        m.app.dependency_overrides[get_db] = lambda: mock_db
 
        response = await async_client.get(f"/notifications/{ALERT_ID}", headers=auth_headers)
 
        assert response.status_code == 403
 
    @pytest.mark.asyncio
    async def test_alert_not_found_returns_404(self, async_client, admin_headers):
        mock_db = _make_mock_db(alert=None, camera=None)
        m.app.dependency_overrides[get_db] = lambda: mock_db
 
        headers = _headers_for_neighbourhood(admin_headers)
        response = await async_client.get(f"/notifications/{ALERT_ID}", headers=headers)
 
        assert response.status_code == 404
 
    @pytest.mark.asyncio
    async def test_alert_in_other_neighbourhood_forbidden(self, async_client, admin_headers):
        alert = _make_alert()
        camera = _make_camera(neighbourhood_id=uuid.uuid4())
        mock_db = _make_mock_db(alert=alert, camera=camera)
        m.app.dependency_overrides[get_db] = lambda: mock_db
 
        headers = _headers_for_neighbourhood(admin_headers)
        response = await async_client.get(f"/notifications/{ALERT_ID}", headers=headers)
 
        assert response.status_code == 403
 
    @pytest.mark.asyncio
    async def test_missing_camera_forbidden(self, async_client, admin_headers):
        alert = _make_alert()
        mock_db = _make_mock_db(alert=alert, camera=None)
        m.app.dependency_overrides[get_db] = lambda: mock_db
 
        headers = _headers_for_neighbourhood(admin_headers)
        response = await async_client.get(f"/notifications/{ALERT_ID}", headers=headers)
 
        assert response.status_code == 403
 
    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self, async_client):
        response = await async_client.get(f"/notifications/{ALERT_ID}")
 
        assert response.status_code in (401, 403)