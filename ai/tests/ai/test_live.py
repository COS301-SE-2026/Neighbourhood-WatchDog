import os
from dotenv import load_dotenv

os.environ["MKL_THREADING_LAYER"] = "GNU"


import cv2 # noqa: E402

from ultralytics import YOLO # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))

load_dotenv(os.path.join(AI_DIR, ".env"))
load_dotenv(os.path.join(AI_DIR, "..", ".env"))

threat_model = YOLO(os.path.join(AI_DIR, "pipeline/models/weights/best.pt"))
person_model = YOLO(os.path.join(AI_DIR, "pipeline/models/weights/yolov8n.pt"))

RTSP_URL = os.getenv("WATCHDOG_TEST_RTSP_URL")

if not RTSP_URL:
    raise RuntimeError(
        "WATCHDOG_TEST_RTSP_URL is not configured. "
        "Add it to ai/.env before running this test."
    )

print("Models loaded: ", threat_model.names, person_model.names.get(0))
print("Connecting to camera ... (Ctrl+C to stop)")



cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Could not connect to RTSP stream")
    exit(1)

print("Camera connected - detecting...")


frame_count = 0
while True:
    ret, frame = cap.read()
    
    if not ret:
        print("No frame recieved")
        continue


    frame_count += 1
    if frame_count % 3 != 0:  #processing every third frame
        continue



    #threat detection
    threat_results = threat_model.predict(
        frame,
        imgsz=640, 
        conf=0.6,
        verbose=False
    )
    
    for box in threat_results[0].boxes:
        label = threat_model.names[int(box.cls[0])]
        conf = float(box.conf[0])
        print(f"THREAT: {label} ({conf:.0%})")


    
    #human detection
    person_results = person_model.predict(
        frame,
        imgsz=640,
        conf=0.6,
        classes=[0],
        verbose=False
    )

    for box in person_results[0].boxes:
        conf = float(box.conf[0])
        print(f"PERSON DETECTED ({conf:.0%})")





cap.release()

