import cv2
import numpy as np
from datetime import datetime


def annotate_frame(frame: np.ndarray, tracks: list) -> np.ndarray:
    annotated = frame.copy()

    for track in tracks:
        x1, y1, x2, y2 = [int(v) for v in track['bbox']]
        track_id = track['track_id']
        confidence = track['confidence']


        #drawing the boundary box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

        #drawing the label
        label = f"ID:{track_id} {confidence:.2f}"
        cv2.putText(
            annotated,
            label,
            (x1, y1-10),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.5,
            (0, 255, 0), 
            2
        )