import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort


PERSON_CLASS = 0

class Detector:
    def __init__(self, weights_path: str, conf: float=0.6, iou: float=0.3):
        self.model = YOLO(weights_path)
        self.conf = conf
        self.iou = iou

        self.tracker = DeepSort(
            max_age=70,
            n_init=2,
            max_iou_distance=0.7,
            embedder="mobilenet",
            embedder_gpu=False
        )

    def process_frame(self, frame) -> list:
        results = self.model.predict(
            frame,
            verbose=False, 
            conf=self.conf, 
            iou=self.iou,
            # tracker="bytetrack.yaml",
            # persist=True,
            imgsz=640,
        )

        detections = []
        for box in results[0].boxes:
            if int(box.cls[0]) == PERSON_CLASS:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                detections.append((
                    [x1, y1, x2-x1, y2-y1],
                    confidence, 
                    "person"
                ))

        tracks = self.tracker.update_tracks(detections, frame=frame)

        confirmed = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            confirmed.append({
                'track_id': track.track_id,
                'confidence': track.det_conf if track.det_conf is not None else 0.0,
                'bbox': track.to_ltrb().tolist()
            })

        return confirmed

        # return detections