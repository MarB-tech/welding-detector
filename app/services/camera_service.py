import cv2
from app.core import settings


class CameraService:
    def __init__(self, camera_index=None):
        # Jeśli nie podano indexu, użyj z settings
        if camera_index is None:
            camera_index = settings.CAMERA_INDEX
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