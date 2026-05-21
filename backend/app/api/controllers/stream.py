import os
import cv2
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

router = APIRouter(prefix="/stream", tags=["stream"])

def mjpeg_generator(rtsp_url: str):
    
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            yield(
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )
    finally:
        cap.release()

@router.get("/")
def stream(url: str):
    return StreamingResponse(
        mjpeg_generator(url),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/health")
def stream_health(url: str):
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    try:
        is_available = cap.isOpened()
        if is_available:
            is_available = cap.grab()
        return {"available": bool(is_available)}
    finally:
        cap.release()