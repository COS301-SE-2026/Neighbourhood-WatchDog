import cv2
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

from ultralytics import YOLO

PERSON_CLASS = 0

class Detector:
    def __init__(self, weights_path: str, conf: float=0.6, iou: float=0.3):
        self.model = YOLO(weights_path)
        self.conf = conf
        self.iou = iou

    def process_frame(self, frame) -> list:
        results = self.model.track(
            frame,
            verbose=False, 
            conf=self.conf, 
            iou=self.iou,
            tracker="bytetrack.yaml",
            persist=True,
        )

        detections = []
        for box in results[0].boxes:
            if int(box.cls[0]) == PERSON_CLASS and box.id is not None:
                   detections.append({
                        'track_id': int(box.id[0]),
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist()
                   })

        return detections