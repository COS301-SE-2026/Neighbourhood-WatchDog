import pytest
from uuid import uuid4
from unittest.mock import Mock, patch
from app.services.camera_service import register_camera_handler
from app.services.camera_service import RegisterCameraReq
from app.models.camera import CameraVisibilityEnum
from fastapi import HTTPException
from datetime import datetime

class TestRegisterCamera:
    def setup_method(self):
        """Arrange"""
        self.mock_db = Mock()

        self.mock_property = Mock()
        self.property_id = uuid4()

        self.mock_property_user = Mock()
        self.mock_property_user.user = Mock()
        self.mock_property_user.user.cognito_sub = "user-sub-123"

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_property,
            self.mock_property_user
        ]

        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

        self.mock_camera = Mock()
        self.mock_camera.id = uuid4()
        self.mock_camera.rtsp_url="rtsp://example.com/stream"
        self.mock_camera.location="Front Door"
        self.mock_camera.visibility=CameraVisibilityEnum.PRIVATE
        self.mock_camera.property_id=uuid4()
        self.mock_camera.neighbourhood_id = uuid4()
        self.mock_camera.created_at = datetime.now()
        
        self.mock_req = RegisterCameraReq(
            rtsp_url="rtsp://admin:securepassword123@192.168.1.100:554/Streaming/channels/101",
            location="Front Door",
            visibility=CameraVisibilityEnum.PRIVATE,
            property_id=uuid4()
        )

        self.claims = {"sub" : "user-sub-123"}

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
            assert camera.rtsp_url == "rtsp://example.com/stream"
            assert camera.location == "Front Door"
            assert camera.visibility == CameraVisibilityEnum.PRIVATE
            assert camera.property_id == self.mock_camera.property_id
            assert camera.created_at == self.mock_camera.created_at
            assert camera.neighbourhood_id == self.mock_camera.neighbourhood_id

            assert self.mock_db.add.call_count == 1
            assert self.mock_db.flush.call_count == 0
            assert self.mock_db.refresh.call_count == 0
            assert self.mock_db.commit.call_count == 1
            assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_db_none(self):
        with patch('app.services.camera_service.Camera') as MockCamera:

            MockCamera.return_value = self.mock_camera

            self.mock_req = RegisterCameraReq(
                rtsp_url="rtsp://admin:securepassword123@192.168.1.100:554/Streaming/channels/101",
                location="Front Door",
                visibility=CameraVisibilityEnum.PRIVATE,
                property_id=uuid4()
            )
            
            with pytest.raises(HTTPException) as exception:
                await register_camera_handler(
                    req = self.mock_req,
                    db = None,
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