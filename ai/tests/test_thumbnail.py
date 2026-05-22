import cv2
import os
from ai.pipeline.utils.thumbnail import annotate_frame, encode_frame_as_jpeg

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
url = "rtsp://Intrepid:password@192.168.1.126:554/stream2"


cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
if not cap.isOpened():
    raise SystemExit("Failed to open stream")


while True:
    ret, frame = cap.read()
    if not ret:
        break


    tracks = [{
        'track_id': 1,
        'confidence': 0.9,
        'bbox': [50, 50, 250, 350]
    }]

    annotated = annotate_frame(frame, tracks)

    jpeg_bytes = encode_frame_as_jpeg(annotated)

    cv2.imshow("thumbnail", annotated)
    if cv2.waitKey(1) & 0XFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


# # create a blank test frame
# frame = np.zeros((360, 640, 3), dtype=np.uint8)

# # mock tracks
# tracks = [
#     {'track_id': 4, 'confidence': 0.76, 'bbox': [100, 100, 300, 350]},
#     {'track_id': 5, 'confidence': 0.68, 'bbox': [400, 80, 580, 320]},
# ]

# # annotate
# annotated = annotate_frame(frame, tracks)

# # encode
# jpeg_bytes = encode_frame_as_jpeg(annotated)

# # save to disk to visually verify
# cv2.imwrite('ai/tests/test_thumbnail_output.jpg', annotated)

# print(f"Annotated frame shape: {annotated.shape}")
# print(f"JPEG size: {len(jpeg_bytes)} bytes")
