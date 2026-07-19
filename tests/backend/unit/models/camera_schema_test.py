from pydantic import ValidationError
import pytest
from uuid import uuid4
from app.schemas.camera import RegisterCameraReq, CameraRes, RegisterCameraRes
from app.models.camera import CameraVisibilityEnum
from datetime import datetime

TEST_RTSP_URL = "rtsp://192.168.2.10:554/stream"
FRONT_DOOR = "Front Door"

class TestRegisterCameraReq:
    def test_valid_request(self):
        """Happy path"""
        property_id = uuid4()
        req = RegisterCameraReq(
            rtsp_url="rtsp://admin:password@192.168.2.10:554/Streaming/channels/101",
            location=FRONT_DOOR,
            visibility=CameraVisibilityEnum.PRIVATE,
            property_id=property_id
        )
        assert req.rtsp_url == "rtsp://admin:password@192.168.2.10:554/Streaming/channels/101"
        assert req.location == FRONT_DOOR
        assert req.visibility == CameraVisibilityEnum.PRIVATE
        assert req.property_id == property_id

    def test_missing_rtsp_url(self):
        """Test missing RTSP URL raises ValidationError"""
        with pytest.raises(ValidationError):
            RegisterCameraReq(
                rtsp_url=None,
                location=FRONT_DOOR,
                visibility=CameraVisibilityEnum.PRIVATE,
                property_id=uuid4()
            )

    def test_missing_property_id(self):
        """Test missing property_id raises ValidationError"""
        with pytest.raises(ValidationError):
            RegisterCameraReq(
                rtsp_url=TEST_RTSP_URL,
                location=FRONT_DOOR,
                visibility=CameraVisibilityEnum.PRIVATE,
                property_id=None
            )

    def test_empty_location(self):
        """Test empty location raises ValidationError"""
        with pytest.raises(ValidationError):
            RegisterCameraReq(
                rtsp_url=TEST_RTSP_URL,
                location="",
                visibility=CameraVisibilityEnum.PRIVATE,
                property_id=uuid4()
            )

    def test_invalid_visibility(self):
        """Test invalid visibility value raises ValidationError"""
        with pytest.raises(ValidationError):
            RegisterCameraReq(
                rtsp_url=TEST_RTSP_URL,
                location=FRONT_DOOR,
                visibility="INVALID",
                property_id=uuid4()
            )


class TestCameraRes:
    def test_valid_camera_response(self):
        """Happy path"""
        camera_id = uuid4()
        property_id = uuid4()
        neighbourhood_id = uuid4()
        now = datetime.now()

        model = CameraRes(
            id=camera_id,
            property_id=property_id,
            neighbourhood_id=neighbourhood_id,
            visibility=CameraVisibilityEnum.PRIVATE,
            location=FRONT_DOOR,
            rtsp_url=TEST_RTSP_URL,
            created_at=now
        )
        assert model.id == camera_id
        assert model.location == FRONT_DOOR
        assert model.visibility == CameraVisibilityEnum.PRIVATE

    def test_missing_location(self):
        """Test missing location raises ValidationError"""
        with pytest.raises(ValidationError):
            CameraRes(
                id=uuid4(),
                property_id=uuid4(),
                neighbourhood_id=uuid4(),
                visibility=CameraVisibilityEnum.PRIVATE,
                location=None,
                rtsp_url=TEST_RTSP_URL,
                created_at=datetime.now()
            )

    def test_empty_rtsp_url(self):
        """Test empty RTSP URL raises ValidationError"""
        with pytest.raises(ValidationError):
            CameraRes(
                id=uuid4(),
                property_id=uuid4(),
                neighbourhood_id=uuid4(),
                visibility=CameraVisibilityEnum.PRIVATE,
                location=FRONT_DOOR,
                rtsp_url="",
                created_at=datetime.now()
            )


class TestRegisterCameraRes:
    def test_response_with_data(self):
        """Happy path with camera data"""
        camera_data = CameraRes(
            id=uuid4(),
            property_id=uuid4(),
            neighbourhood_id=uuid4(),
            visibility=CameraVisibilityEnum.PRIVATE,
            location=FRONT_DOOR,
            rtsp_url=TEST_RTSP_URL,
            created_at=datetime.now()
        )
        response = RegisterCameraRes(
            status=201,
            message="Camera registered successfully",
            data=camera_data
        )
        assert response.status == 201
        assert response.data is not None

    def test_response_with_none_fields(self):
        """Test response with optional None fields"""
        response = RegisterCameraRes(status=400)
        assert response.status == 400
        assert response.message is None
        assert response.data is None
