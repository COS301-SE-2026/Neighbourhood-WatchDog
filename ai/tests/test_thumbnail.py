import cv2
import numpy as np
from ai.pipeline.utils.thumbnail import annotate_frame, encode_frame_as_jpeg

# create a blank test frame
frame = np.zeros((360, 640, 3), dtype=np.uint8)

# mock tracks
tracks = [
    {'track_id': 4, 'confidence': 0.76, 'bbox': [100, 100, 300, 350]},
    {'track_id': 5, 'confidence': 0.68, 'bbox': [400, 80, 580, 320]},
]

# annotate
annotated = annotate_frame(frame, tracks)

# encode
jpeg_bytes = encode_frame_as_jpeg(annotated)

# save to disk to visually verify
cv2.imwrite('ai/tests/test_thumbnail_output.jpg', annotated)

print(f"Annotated frame shape: {annotated.shape}")
print(f"JPEG size: {len(jpeg_bytes)} bytes")
print("Saved to ai/tests/test_thumbnail_output.jpg — open it to verify")