import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from app.services.camera_service import register_camera_handler, deregister_camera_handler, edit_camera_handler, list_enabled_cameras_for_agent_handler
from app.services.camera_service import CameraEditReq
from app.schemas.camera import RegisterCameraReq
from app.models.camera import CameraVisibilityEnum
from fastapi import HTTPException
from datetime import datetime

import app.services.camera_service as camera_service_module

from app.schemas.camera import MediaMtxAuthRequest
from sqlalchemy.exc import IntegrityError

MOCK_RTSP_URL = "rtsp://example.com/stream"
MOCK_CAMERA_NAME = "Camera 1"

@pytest.fixture(autouse=True)
def mock_audit():
    with patch(
        "app.services.camera_service.create_audit_log_item",
        new=AsyncMock(),
    ):
        yield

@pytest.fixture(autouse=True)
def mock_invalidate_camera_caches():
    with patch(
        "app.services.camera_service.invalidate_camera_caches",
        new_callable=AsyncMock,
    ) as mock_invalidate_camera_caches:
        yield mock_invalidate_camera_caches

def make_mock_db():
    mock_db = Mock()
    mock_result = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = Mock()
    mock_db.delete = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.rollback = AsyncMock()
    return mock_db, mock_result

class TestRegisterCamera:
    def setup_method(self):
        """Arrange"""
        self.mock_db, self.mock_result = make_mock_db()

        self.mock_property = Mock()
        self.mock_property.neighbourhood_id = uuid4()
        self.property_id = uuid4()

        self.mock_property_user = Mock()
        self.mock_property_user.user = Mock()
        self.mock_property_user.user.cognito_sub = "user-sub-123"

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_property,
            self.mock_property_user
        ]

        self.mock_camera = Mock()
        self.mock_camera.id = uuid4()
        self.mock_camera.name = MOCK_CAMERA_NAME
        self.mock_camera.rtsp_url=MOCK_RTSP_URL
        self.mock_camera.location="Front Door"
        self.mock_camera.visibility=CameraVisibilityEnum.PRIVATE
        self.mock_camera.property_id=uuid4()
        self.mock_camera.enabled = True
        self.mock_camera.neighbourhood_id = self.mock_property.neighbourhood_id
        self.mock_camera.created_at = datetime.now()
        
        self.mock_req = RegisterCameraReq(
            name=MOCK_CAMERA_NAME,
            rtsp_url="rtsp://admin:securepassword123@192.168.1.100:554/Streaming/channels/101",
            location="Front Door",
            visibility=CameraVisibilityEnum.PRIVATE,
            property_id=uuid4()
        )

        self.claims = {
            "id": str(uuid4()),
            "sub": "cognito-sub-123"
        }

    @pytest.mark.asyncio
    async def test_happy_path(self):
        with patch('app.services.camera_service.Camera') as MockCamera:
            #mock camera object is bascially just for when the constructor is called

            MockCamera.return_value = self.mock_camera

            camera = await register_camera_handler(
                req = self.mock_req,
                db = self.mock_db,
                claims = self.claims
            )

            assert camera is not None
            assert camera.id == self.mock_camera.id
            assert camera.name == MOCK_CAMERA_NAME
            assert camera.rtsp_url == MOCK_RTSP_URL
            assert camera.location == "Front Door"
            assert camera.visibility == CameraVisibilityEnum.PRIVATE
            assert camera.property_id == self.mock_camera.property_id
            assert camera.enabled
            assert camera.created_at == self.mock_camera.created_at
            assert camera.neighbourhood_id == self.mock_camera.neighbourhood_id

            assert self.mock_db.add.call_count == 1
            assert self.mock_db.flush.call_count == 1
            assert self.mock_db.refresh.call_count == 1
            assert self.mock_db.commit.call_count == 1
            assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_db_none(self):
        with patch('app.services.camera_service.Camera') as MockCamera:

            MockCamera.return_value = self.mock_camera

            self.mock_req = RegisterCameraReq(
                name=MOCK_CAMERA_NAME,
                rtsp_url="rtsp://admin:securepassword123@192.168.1.100:554/Streaming/channels/101",
                location="Front Door",
                visibility=CameraVisibilityEnum.PRIVATE,
                property_id=uuid4()
            )
            
            with pytest.raises(HTTPException) as exception:
                await register_camera_handler(
                    req = self.mock_req,
                    db=None,
                    claims = self.claims
                )

            assert exception.value.status_code == 500

            assert self.mock_db.add.call_count == 0
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.commit.call_count == 0
            assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_claims_none(self):
        with patch('app.services.camera_service.Camera') as MockCamera:

            MockCamera.return_value = self.mock_camera

            self.mock_req = RegisterCameraReq(
                name=MOCK_CAMERA_NAME,
                rtsp_url="rtsp://admin:securepassword123@192.168.1.100:554/Streaming/channels/101",
                location="Front Door",
                visibility=CameraVisibilityEnum.PRIVATE,
                property_id=uuid4()
            )
            
            with pytest.raises(HTTPException) as exception:
                await register_camera_handler(
                    req = self.mock_req,
                    db = self.mock_db,
                    claims = None,
                )

            assert exception.value.status_code == 401

            assert self.mock_db.add.call_count == 0
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.commit.call_count == 0
            assert self.mock_db.rollback.call_count == 0


class TestDeregisterCamera:
    def setup_method(self):
        """Arrange"""
        self.mock_db, _ = make_mock_db()
        self.camera_id = uuid4()

        self.mock_camera = Mock()
        self.mock_camera.id = self.camera_id
        self.mock_camera.property_id = uuid4()

        self.mock_user = Mock()
        self.mock_user.cognito_sub = "user-sub-123"

        self.mock_prop_user = Mock()
        self.mock_prop_user.user_id = uuid4()
        self.mock_prop_user.user = self.mock_user

        self.mock_camera_result = Mock()
        self.mock_camera_result.scalar_one_or_none.return_value = self.mock_camera

        self.mock_prop_user_result = Mock()
        self.mock_prop_user_result.scalar_one_or_none.return_value = self.mock_prop_user

        self.mock_db.execute = AsyncMock(side_effect=[
            self.mock_camera_result,
            self.mock_prop_user_result,
        ])

        self.mock_db.refresh = AsyncMock()

        self.claims = {
            "id": str(uuid4()),
            "sub": "user-sub-123",
        }

    @pytest.mark.asyncio
    def reset_side_effects(self, camera=None, prop_user=None, user=None):
        """Helper to reset side_effect between tests"""
        self.mock_camera_result = Mock()
        self.mock_camera_result.scalar_one_or_none.return_value = camera

        self.mock_prop_user_result = Mock()
        self.mock_prop_user_result.scalar_one_or_none.return_value = prop_user

        self.mock_db.execute = AsyncMock(side_effect=[
            self.mock_camera_result,
            self.mock_prop_user_result,
        ])

    @pytest.mark.asyncio
    async def test_happy_path(self):
        """Camera exists, user owns it. Deletes successfully"""
        await deregister_camera_handler(
            camera_id=self.camera_id,
            db=self.mock_db,
            claims=self.claims
        )

        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_db_none(self):
        with pytest.raises(HTTPException) as exc:
            await deregister_camera_handler(
                camera_id=self.camera_id,
                db=None,
                claims=self.claims
            )
        assert exc.value.status_code == 500
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_claims_none(self):
        with pytest.raises(HTTPException) as exc:
            await deregister_camera_handler(
                camera_id=self.camera_id,
                db=self.mock_db,
                claims=None
            )
        assert exc.value.status_code == 500
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_camera_not_found(self):
        """Camera ID doesn't exist"""
        self.reset_side_effects(camera=None, prop_user=None)

        with pytest.raises(HTTPException) as exc:
            await deregister_camera_handler(
                camera_id=self.camera_id,
                db=self.mock_db,
                claims=self.claims
            )
        assert exc.value.status_code == 404
        assert self.mock_db.execute.call_count == 1
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1

    @pytest.mark.asyncio
    async def test_wrong_owner(self):
        """Camera belongs to a different user"""

        wrong_user = Mock()
        wrong_user.cognito_sub = "different-user-sub"

        wrong_prop_user = Mock()
        wrong_prop_user.user_id = uuid4()
        wrong_prop_user.user =  wrong_user

        self.reset_side_effects(
            camera=self.mock_camera,
            prop_user=wrong_prop_user,
        )

        with pytest.raises(HTTPException) as exc:
            await deregister_camera_handler(
                camera_id=self.camera_id,
                db=self.mock_db,
                claims=self.claims
            )
        assert exc.value.status_code == 403
        assert self.mock_db.execute.call_count == 2
        assert self.mock_db.commit.call_count == 0
        assert self.mock_db.rollback.call_count == 1


class TestEditCamera:
    def setup_method(self):
        self.mock_db, self.mock_result = make_mock_db()

        self.mock_camera = Mock()
        self.mock_camera.id = uuid4()
        self.mock_camera.rtsp_url=MOCK_RTSP_URL
        self.mock_camera.name = "Camera 1000"
        self.mock_camera.location="Front Door"
        self.mock_camera.visibility=CameraVisibilityEnum.PRIVATE
        self.mock_camera.enabled = True
        self.mock_camera.property_id=uuid4()
        self.mock_camera.neighbourhood_id = uuid4()
        self.mock_camera.created_at = datetime.now()


        self.mock_property_user = Mock()
        self.mock_property_user.user = Mock()
        self.mock_property_user.user.cognito_sub = "user-sub-123"

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_camera,
            self.mock_property_user
        ]

        self.mock_req = CameraEditReq(
            name="Secondary Camera",
            location="Back Door",
            visibility=CameraVisibilityEnum.PUBLIC,
            enabled=False
        )

        self.claims = {
            "id": str(uuid4()),
            "sub": "user-sub-123",
        }

    @pytest.mark.asyncio
    def reset_side_effects(self, camera=None, prop_user=None):
        """Helper to reset side_effect between tests"""
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            camera, prop_user
        ]

    @pytest.mark.asyncio
    async def test_happy_path(self):
        """"Edit camera """
        camera = await edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=self.mock_req,
            db=self.mock_db,
            claims=self.claims
        )


        assert camera is not None
        assert camera.name == "Secondary Camera"
        assert camera.location == "Back Door"
        assert not camera.enabled
        assert camera.visibility == CameraVisibilityEnum.PUBLIC

        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        assert self.mock_db.execute.call_count == 2
        self.mock_db.flush.assert_not_called()
        self.mock_db.rollback.assert_not_called()
        self.mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_payload_raises_400(self):
        """Empty payload on camera"""
        
        empty_req = CameraEditReq()
        with pytest.raises(HTTPException) as exe:
            await edit_camera_handler(
                camera_id=self.mock_camera.id,
                req=empty_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exe.value.status_code == 400
        self.mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_edit(self):
        """Partial edit for a camera"""
        partial_req = CameraEditReq(
            enabled=False
        )
        
        
        camera = await edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=partial_req,
            db=self.mock_db,
            claims=self.claims
        )

        assert camera.name == "Camera 1000"
        assert camera.location == "Front Door"
        assert camera.visibility == CameraVisibilityEnum.PRIVATE
        assert not camera.enabled

        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        assert self.mock_db.execute.call_count == 2
        self.mock_db.flush.assert_not_called()
        self.mock_db.rollback.assert_not_called()
        self.mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_camera_not_found_raises_404(self):
        """Camera non existent for edit camera"""
        self.reset_side_effects(camera=None, prop_user=self.mock_property_user)

        with pytest.raises(HTTPException) as exception:
            await edit_camera_handler(
                camera_id="fake_camera_id",
                req=self.mock_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exception.value.status_code == 404
        self.mock_db.commit.assert_not_called()
        self.mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrong_owner_raises_403(self):
        """Unauthorised user makes request to edit camera"""
        self.reset_side_effects(camera=self.mock_camera, prop_user=None)
        with pytest.raises(HTTPException) as exception:
            await edit_camera_handler(
                camera_id=self.mock_camera.id,
                req=self.mock_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exception.value.status_code == 403
        self.mock_db.commit.assert_not_called()
        self.mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_unexpected_error_raises_500(self):
        """unexpected error, could be db"""

        self.mock_db.commit.side_effect = Exception("DB connection lost")

        with pytest.raises(HTTPException) as exception:
            await edit_camera_handler(
                camera_id=self.mock_camera.id,
                req=self.mock_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exception.value.status_code == 500
        self.mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_re_enable_camera(self):
        """re enabling a camera that has been disabled"""

        self.mock_camera.enabled = False
        enable_req = CameraEditReq(
            enabled=True
        )

        camera = await edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=enable_req,
            db=self.mock_db,
            claims=self.claims
        )

        assert camera.enabled

        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        assert self.mock_db.execute.call_count == 2
        self.mock_db.flush.assert_not_called()
        self.mock_db.rollback.assert_not_called()
        self.mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_called_after_update(self):
        await edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=self.mock_req,
            db=self.mock_db,
            claims=self.claims
        ) 

        self.mock_db.refresh.assert_called_once_with(self.mock_camera)


    @pytest.mark.asyncio
    async def test_enabled_camera_payload_includes_detection_zone_polygons(self):

        property_id = uuid4()
        neighbourhood_id = uuid4()

        camera = MagicMock()
        camera.id = uuid4()
        camera.rtsp_url = "encrypted-value"
        camera.enabled = True
        camera.confidence_threshold = 0.70
        camera.property = MagicMock(neighbourhood_id=neighbourhood_id)
        camera.detection_zones = [
            MagicMock(
                polygon=[
                    [0.1, 0.1],
                    [0.5, 0.1],
                    [0.5, 0.5],
                    [0.1, 0.5]
                ]
            )
        ]

        result = MagicMock()

        result.scalars.return_value.all.return_value = [camera]

        db = MagicMock()

        db.execute = AsyncMock(return_value=result)

        with patch(
            "app.services.camera_service.decrypt_rtsp_url",
            return_value="rtsp://example.test/camera"
        ), patch(
            "app.services.camera_service._camera_publish_credentials",
            return_value=("camera-user", "camera-password")
        ):
            payload = await list_enabled_cameras_for_agent_handler(property_id, db)

        assert len(payload.data) == 1
        assert payload.data[0].confidence_threshold == 0.70
        assert payload.data[0].zones == [
            [
                [0.1, 0.1],
                [0.5, 0.1],
                [0.5, 0.5],
                [0.1, 0.5]
            ]
        ]

def _camera_result(*, scalar=None, rows=None):
    result = Mock()
    result.scalar_one_or_none.return_value = scalar
    result.scalars.return_value.all.return_value = list(rows or [])
    return result


@pytest.mark.asyncio
async def test_publish_master_key_requires_configuration(monkeypatch):
    monkeypatch.delenv("MEDIAMTX_PUBLISH_MASTER_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        camera_service_module._publish_master_key()

    assert str(exc_info.value) == (
        "MEDIAMTX_PUBLISH_MASTER_KEY is not configured."
    )


def test_publish_master_key_and_camera_credentials(monkeypatch):
    monkeypatch.setenv("MEDIAMTX_PUBLISH_MASTER_KEY", "test-master-key")

    camera_id = str(uuid4())

    username, password = (
        camera_service_module._camera_publish_credentials(camera_id)
    )

    assert username == f"camera-{camera_id}"
    assert password
    assert "=" not in password


@pytest.mark.asyncio
async def test_register_camera_rejects_missing_property():
    db, result = make_mock_db()
    result.scalar_one_or_none.return_value = None

    request = RegisterCameraReq(
        name="Test Camera",
        rtsp_url=MOCK_RTSP_URL,
        location="Front Door",
        visibility=CameraVisibilityEnum.PRIVATE,
        property_id=uuid4(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await register_camera_handler(
            req=request,
            db=db,
            claims={"id": str(uuid4()), "sub": "test-sub"},
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Property not found"
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_camera_rolls_back_on_integrity_error():
    db, result = make_mock_db()

    property_obj = Mock()
    property_obj.neighbourhood_id = uuid4()
    result.scalar_one_or_none.return_value = property_obj

    db.flush.side_effect = IntegrityError(
        "insert camera",
        {},
        RuntimeError("duplicate camera"),
    )

    request = RegisterCameraReq(
        name="Test Camera",
        rtsp_url=MOCK_RTSP_URL,
        location="Front Door",
        visibility=CameraVisibilityEnum.PRIVATE,
        property_id=uuid4(),
    )

    with patch(
        "app.services.camera_service.Camera"
    ) as mock_camera:
        mock_camera.return_value = Mock(
            id=uuid4(),
            name="Test Camera",
            property_id=request.property_id,
            rtsp_url=MOCK_RTSP_URL,
            location="Front Door",
            visibility=CameraVisibilityEnum.PRIVATE,
            enabled=True,
            created_at=datetime.now(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await register_camera_handler(
                req=request,
                db=db,
                claims={"id": str(uuid4()), "sub": "test-sub"},
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Could not register camera"
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_deregister_camera_handles_integrity_error():
    db, _ = make_mock_db()

    camera = Mock(
        id=uuid4(),
        property_id=uuid4(),
        name="Camera",
        visibility=CameraVisibilityEnum.PRIVATE,
        location="Gate",
    )
    user = Mock(cognito_sub="test-sub")
    property_user = Mock(user=user)

    db.execute = AsyncMock(
        side_effect=[
            _camera_result(scalar=camera),
            _camera_result(scalar=property_user),
        ]
    )
    db.commit.side_effect = IntegrityError(
        "delete camera",
        {},
        RuntimeError("constraint"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await deregister_camera_handler(
            camera_id=camera.id,
            db=db,
            claims={"id": str(uuid4()), "sub": "test-sub"},
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Could not deregister camera"
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_deregister_camera_handles_unexpected_error():
    db, _ = make_mock_db()

    camera = Mock(
        id=uuid4(),
        property_id=uuid4(),
        name="Camera",
        visibility=CameraVisibilityEnum.PRIVATE,
        location="Gate",
    )
    user = Mock(cognito_sub="test-sub")
    property_user = Mock(user=user)

    db.execute = AsyncMock(
        side_effect=[
            _camera_result(scalar=camera),
            _camera_result(scalar=property_user),
        ]
    )
    db.commit.side_effect = RuntimeError("database unavailable")

    with pytest.raises(HTTPException) as exc_info:
        await deregister_camera_handler(
            camera_id=camera.id,
            db=db,
            claims={"id": str(uuid4()), "sub": "test-sub"},
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to delete camera"
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_cameras_returns_accessible_property_cameras():
    property_id = uuid4()
    neighbourhood_id = uuid4()
    camera_id = uuid4()

    property_obj = Mock(neighbourhood_id=neighbourhood_id)
    property_user = Mock()
    camera = Mock()
    camera.id = camera_id
    camera.property_id = property_id
    camera.name = "Front Camera"
    camera.visibility = CameraVisibilityEnum.PUBLIC
    camera.location = "Front Gate"
    camera.enabled = True
    camera.created_at = datetime.now()
    camera.rtsp_url = "encrypted-value"

    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            _camera_result(scalar=property_obj),
            _camera_result(scalar=property_user),
            _camera_result(rows=[camera]),
        ]
    )

    with patch(
        "app.services.camera_service.decrypt_rtsp_url",
        return_value=MOCK_RTSP_URL,
    ):
        response = await camera_service_module.list_cameras_handler(
            property_id=str(property_id),
            db=db,
            claims={"sub": "test-sub"},
        )

    assert response.status == 200
    assert len(response.data) == 1
    assert response.data[0].id == camera_id
    assert response.data[0].property_id == property_id
    assert response.data[0].neighbourhood_id == neighbourhood_id
    assert response.data[0].name == "Front Camera"
    assert response.data[0].enabled is True


@pytest.mark.asyncio
async def test_list_cameras_rejects_invalid_property_id():
    db = Mock()
    db.execute = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await camera_service_module.list_cameras_handler(
            property_id="not-a-uuid",
            db=db,
            claims={"sub": "test-sub"},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid property ID"
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_cameras_rejects_missing_property():
    db = Mock()
    db.execute = AsyncMock(
        return_value=_camera_result(scalar=None)
    )

    with pytest.raises(HTTPException) as exc_info:
        await camera_service_module.list_cameras_handler(
            property_id=str(uuid4()),
            db=db,
            claims={"sub": "test-sub"},
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Property does not exist"


@pytest.mark.asyncio
async def test_list_cameras_rejects_user_without_property_access():
    db = Mock()
    db.execute = AsyncMock(
        side_effect=[
            _camera_result(scalar=Mock(neighbourhood_id=None)),
            _camera_result(scalar=None),
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await camera_service_module.list_cameras_handler(
            property_id=str(uuid4()),
            db=db,
            claims={"sub": "test-sub"},
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "This user does not have access to this property"
    )


@pytest.mark.asyncio
async def test_mediamtx_allows_read_and_playback():
    db = Mock()

    read_response = await (
        camera_service_module.authorize_mediamtx_for_agent_handler(
            MediaMtxAuthRequest(action="read"),
            db,
        )
    )
    playback_response = await (
        camera_service_module.authorize_mediamtx_for_agent_handler(
            MediaMtxAuthRequest(action="playback"),
            db,
        )
    )

    assert read_response.status_code == 204
    assert playback_response.status_code == 204


@pytest.mark.asyncio
async def test_mediamtx_rejects_unknown_action():
    db = Mock()

    with pytest.raises(HTTPException) as exc_info:
        await (
            camera_service_module.authorize_mediamtx_for_agent_handler(
                MediaMtxAuthRequest(action="unknown"),
                db,
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "This MediaMTX action is not allowed."
    )


@pytest.mark.asyncio
async def test_mediamtx_rejects_invalid_publish_path():
    db = Mock()

    with pytest.raises(HTTPException) as exc_info:
        await (
            camera_service_module.authorize_mediamtx_for_agent_handler(
                MediaMtxAuthRequest(
                    action="publish",
                    path="invalid/path",
                ),
                db,
            )
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Publish path mist be cameras/<camera-uuid>."
    )


@pytest.mark.asyncio
async def test_mediamtx_rejects_missing_camera():
    camera_id = uuid4()
    db = Mock()
    db.execute = AsyncMock(
        return_value=_camera_result(scalar=None)
    )

    with pytest.raises(HTTPException) as exc_info:
        await (
            camera_service_module.authorize_mediamtx_for_agent_handler(
                MediaMtxAuthRequest(
                    action="publish",
                    path=f"cameras/{camera_id}",
                    user="camera-user",
                    password="camera-password",
                ),
                db,
            )
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Camera does not exist or is disabled."
    )


@pytest.mark.asyncio
async def test_mediamtx_rejects_invalid_credentials():
    camera_id = uuid4()
    camera = Mock(id=camera_id)

    db = Mock()
    db.execute = AsyncMock(
        return_value=_camera_result(scalar=camera)
    )

    with patch(
        "app.services.camera_service._camera_publish_credentials",
        return_value=("expected-user", "expected-password"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await (
                camera_service_module.authorize_mediamtx_for_agent_handler(
                    MediaMtxAuthRequest(
                        action="publish",
                        path=f"cameras/{camera_id}",
                        user="wrong-user",
                        password="wrong-password",
                    ),
                    db,
                )
            )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Invalid publish credential for the requested camera path."
    )


@pytest.mark.asyncio
async def test_mediamtx_accepts_valid_publish_credentials():
    camera_id = uuid4()
    camera = Mock(id=camera_id)

    db = Mock()
    db.execute = AsyncMock(
        return_value=_camera_result(scalar=camera)
    )

    with patch(
        "app.services.camera_service._camera_publish_credentials",
        return_value=("expected-user", "expected-password"),
    ):
        response = (
            await camera_service_module.authorize_mediamtx_for_agent_handler(
                MediaMtxAuthRequest(
                    action="publish",
                    path=f"cameras/{camera_id}",
                    user="expected-user",
                    password="expected-password",
                ),
                db,
            )
        )

    assert response.status_code == 204