from ultralytics import YOLO

model = YOLO("pipeline/models/weights/best.pt")   # ← no "ai/" prefix

print(model.names)  

model("rtsp://Intrepid:password1234@192.168.3.65:554/stream2", stream=True, show=True)