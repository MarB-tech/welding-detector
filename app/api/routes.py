from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.remote_camera_service import RemoteCameraService

router = APIRouter()
camera_service = RemoteCameraService()

@router.get("/stream")
async def stream():
    return StreamingResponse(
        camera_service.get_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/health")
async def health():
    camera_status = await camera_service.health_check()
    return {"api": "healthy", "camera_service": camera_status}