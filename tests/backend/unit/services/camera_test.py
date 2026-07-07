import pytest
from uuid import uuid4
import unittest
from unittest.mock import Mock, patch
from app.services.camera_service import register_camera_handler, deregister_camera_handler, edit_camera_handler
from app.services.camera_service import RegisterCameraReq, CameraEditReq
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
        self.mock_camera.name = "Camera 1"
        self.mock_camera.rtsp_url="rtsp://example.com/stream"
        self.mock_camera.location="Front Door"
        self.mock_camera.visibility=CameraVisibilityEnum.PRIVATE
        self.mock_camera.property_id=uuid4()
        self.mock_camera.enabled = True
        self.mock_camera.neighbourhood_id = uuid4()
        self.mock_camera.created_at = datetime.now()
        
        self.mock_req = RegisterCameraReq(
            name="Camera 1",
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
            assert camera.name == "Camera 1"
            assert camera.rtsp_url == "rtsp://example.com/stream"
            assert camera.location == "Front Door"
            assert camera.visibility == CameraVisibilityEnum.PRIVATE
            assert camera.property_id == self.mock_camera.property_id
            assert camera.enabled == True
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
                name="Camera 1",
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
                name="Camera 1",
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
        self.mock_db = Mock()
        self.camera_id = uuid4()

        self.mock_camera = Mock()
        self.mock_camera.id = self.camera_id
        self.mock_camera.property_id = uuid4()

        self.mock_prop_user = Mock()
        self.mock_prop_user.user.cognito_sub = "user-sub-123"

        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            self.mock_camera,
            self.mock_prop_user
        ]

        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

        self.claims = {"sub": "user-sub-123"}


    def reset_side_effects(self, camera=None, prop_user=None):
        """Helper to reset side_effect between tests"""
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            camera, prop_user
        ]

    @pytest.mark.asyncio
    async def test_happy_path(self):
        """Camera exists, user owns it. Deletes successfully"""
        deregister_camera_handler(
            camera_id=self.camera_id,
            db=self.mock_db,
            claims=self.claims
        )

        assert self.mock_db.execute.call_count == 3  
        assert self.mock_db.commit.call_count == 1
        assert self.mock_db.rollback.call_count == 0

    @pytest.mark.asyncio
    async def test_db_none(self):
        with pytest.raises(HTTPException) as exc:
            deregister_camera_handler(
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
            deregister_camera_handler(
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
            deregister_camera_handler(
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
        self.mock_prop_user.user.cognito_sub = "different-user-sub"
        self.reset_side_effects(camera=self.mock_camera, prop_user=self.mock_prop_user)

        with pytest.raises(HTTPException) as exc:
            deregister_camera_handler(
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
        self.mock_db = Mock()

        self.mock_camera = Mock()
        self.mock_camera.id = uuid4()
        self.mock_camera.rtsp_url="rtsp://example.com/stream"
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

        self.mock_db.add = Mock()
        self.mock_db.flush = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.rollback = Mock()

        self.mock_req = CameraEditReq(
            name="Secondary Camera",
            location="Back Door",
            visibility=CameraVisibilityEnum.PUBLIC,
            enabled=False
        )

        self.claims = {"sub" : "user-sub-123"}

    def reset_side_effects(self, camera=None, prop_user=None):
        """Helper to reset side_effect between tests"""
        self.mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            camera, prop_user
        ]

    def test_happy_path(self):
        """"Edit camera """
        camera = edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=self.mock_req,
            db=self.mock_db,
            claims=self.claims
        )


        assert camera is not None
        assert camera.name == "Secondary Camera"
        assert camera.location == "Back Door"
        assert camera.enabled == False
        assert camera.visibility == CameraVisibilityEnum.PUBLIC

        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        self.mock_db.execute.call_count == 2
        self.mock_db.flush.assert_not_called()
        self.mock_db.rollback.assert_not_called()
        self.mock_db.add.assert_not_called()

    def test_empty_payload_raises_400(self):
        """Empty payload on camera"""
        
        empty_req = CameraEditReq()
        with pytest.raises(HTTPException) as exe:
            camera = edit_camera_handler(
                camera_id=self.mock_camera.id,
                req=empty_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exe.value.status_code == 400
        self.mock_db.rollback.assert_called_once()

    def test_partial_edit(self):
        """Partial edit for a camera"""
        partial_req = CameraEditReq(
            enabled=False
        )
        
        
        camera = edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=partial_req,
            db=self.mock_db,
            claims=self.claims
        )

        assert camera.name == "Camera 1000"
        assert camera.location == "Front Door"
        assert camera.visibility == CameraVisibilityEnum.PRIVATE
        assert camera.enabled == False

        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        self.mock_db.execute.call_count == 2
        self.mock_db.flush.assert_not_called()
        self.mock_db.rollback.assert_not_called()
        self.mock_db.add.assert_not_called()

    def test_camera_not_found_raises_404(self):
        """Camera non existent for edit camera"""
        self.reset_side_effects(camera=None, prop_user=self.mock_property_user)

        with pytest.raises(HTTPException) as exception:
            camera = edit_camera_handler(
                camera_id="fake_camera_id",
                req=self.mock_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exception.value.status_code == 404
        self.mock_db.commit.assert_not_called()
        self.mock_db.rollback.assert_called_once()

    
    def test_wrong_owner_raises_403(self):
        """Unauthorised user makes request to edit camera"""
        self.reset_side_effects(camera=self.mock_camera, prop_user=None)
        with pytest.raises(HTTPException) as exception:
            camera = edit_camera_handler(
                camera_id=self.mock_camera.id,
                req=self.mock_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exception.value.status_code == 403
        self.mock_db.commit.assert_not_called()
        self.mock_db.rollback.assert_called_once()

    def test_unexpected_error_raises_500(self):
        """unexpected error, could be db"""

        self.mock_db.commit.side_effect = Exception("DB connection lost")

        with pytest.raises(HTTPException) as exception:
            camera = edit_camera_handler(
                camera_id=self.mock_camera.id,
                req=self.mock_req,
                db=self.mock_db,
                claims=self.claims
            )

        assert exception.value.status_code == 500
        self.mock_db.rollback.assert_called_once()

    def test_re_enable_camera(self):
        """re enabling a camera that has been disabled"""

        self.mock_camera.enabled = False
        enable_req = CameraEditReq(
            enabled=True
        )

        camera = edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=enable_req,
            db=self.mock_db,
            claims=self.claims
        )

        assert camera.enabled == True

        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        self.mock_db.execute.call_count == 2
        self.mock_db.flush.assert_not_called()
        self.mock_db.rollback.assert_not_called()
        self.mock_db.add.assert_not_called()

    def test_refresh_called_after_update(self):
        edit_camera_handler(
            camera_id=self.mock_camera.id,
            req=self.mock_req,
            db=self.mock_db,
            claims=self.claims
        )

        self.mock_db.refresh.assert_called_once_with(self.mock_camera)



