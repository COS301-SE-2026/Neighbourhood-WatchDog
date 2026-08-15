from unittest.mock import MagicMock, patch

from camera_runtime import CameraSupervisor


CAMERA_ID = "40000000-0000-0000-0000-000000000001"
ZONE = [
    [0.1, 0.1],
    [0.5, 0.1],
    [0.5, 0.5],
    [0.1, 0.5]
]


def no_op_detection_target(camera, rtsp_url, stop_event):
    return None


def test_enabled_camera_payload_maps_zones_and_threshold_to_camera_spec():

    response = MagicMock()

    response.json.return_value = {
        "data": [
            {
                "id": CAMERA_ID,
                "rtsp_url": "rtsp://example.test/camera",
                "enabled": True,
                "neighbourhood_id": "50000000-0000-0000-0000-000000000001",
                "confidence_threshold": 0.70,
                "zones": [ZONE],
                "publish_username": "camera-user",
                "publish_password": "camera-password"
            }
        ]
    }

    supervisor = CameraSupervisor(
        backend_url="http://backend:8000",
        internal_token="unused",
        mediamtx_rtsp_url="rtsp://mediamtx:8554",
        detection_target=no_op_detection_target
    )

    with patch(
        "camera_runtime.keyring.get_password",
        return_value="test-agent-key"
    ), patch(
        "camera_runtime.httpx.get",
        return_value=response
    ):
        cameras = supervisor._fetch_enabled_cameras()

    camera = cameras[CAMERA_ID]

    assert camera.confidence_threshold == 0.70
    
    assert camera.zones == (
        (
            (0.1, 0.1),
            (0.5, 0.1),
            (0.5, 0.5),
            (0.1, 0.5)
        )
    )