import cv2

class CameraService:
    def __init__(self, camera_index=1):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Nie udało się otworzyć kamery {camera_index}")

    def get_frame(self):
        success, frame = self.cap.read()
        if not success:
            return None
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

    def release(self):
        self.cap.release()