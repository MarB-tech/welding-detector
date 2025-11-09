from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.camera_service import CameraService
import time

router = APIRouter()
camera = CameraService()

def generate_frames():
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            # Jeśli nie ma klatki, czekaj chwilę
            time.sleep(0.1)

@router.get("/stream")
def stream():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
