import cv2

class StreamCapture:
    def __init__(self, url: str):
        self.cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

        if not self.cap.isOpened():
            raise ConnectionError(f"Failed to open stream: {url}")
        print(f"Stream opened: {url}")


    def read_frame(self):
        ret, frame = self.cap.read()

        return frame if ret else None
    
    def release(self):
        self.cap.release()