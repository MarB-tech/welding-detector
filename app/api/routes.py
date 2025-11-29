"""
API Routes - Endpointy kamery i nagrywania.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response, FileResponse

from app.services.remote_camera_service import RemoteCameraService, get_camera_service
from app.services.frame_overlay_service import FrameOverlayService, get_overlay_service
from app.services.video_recorder_service import VideoRecorderService, get_recorder_service
from app.api.models import (
    CameraHealthResponse, HealthStatus,
    RecordingStatusResponse, RecordingStartResponse, RecordingStopResponse, RecordingListResponse
)

camera_router = APIRouter(prefix="/camera", tags=["Camera"])
edge_router = APIRouter(prefix="/edge", tags=["Edge Detection"])
recording_router = APIRouter(prefix="/recording", tags=["Recording"])


# ============== CAMERA ==============

@camera_router.get("/stream")
async def stream_camera(
    overlay: bool = Query(True),
    camera: RemoteCameraService = Depends(get_camera_service),
    overlay_svc: FrameOverlayService = Depends(get_overlay_service),
    recorder: VideoRecorderService = Depends(get_recorder_service)
):
    """Stream MJPEG z timestampem i wskaźnikiem REC."""
    async def generate():
        async for frame in camera.stream_frames():
            if overlay:
                frame = overlay_svc.apply_overlay_to_jpeg(frame)
            
            # Zapis do wideo gdy nagrywanie aktywne
            if recorder.is_recording:
                recorder.add_frame(frame)
            
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
    
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@camera_router.get("/capture")
async def capture_frame(
    overlay: bool = Query(True),
    camera: RemoteCameraService = Depends(get_camera_service),
    overlay_svc: FrameOverlayService = Depends(get_overlay_service)
):
    """Pojedyncza klatka JPEG z timestampem."""
    frame = await camera.get_single_frame()
    if not frame:
        raise HTTPException(503, "Nie można pobrać klatki z kamery")
    
    if overlay:
        frame = overlay_svc.apply_overlay_to_jpeg(frame)
    
    return Response(frame, media_type="image/jpeg")


@camera_router.get("/health", response_model=CameraHealthResponse)
async def camera_health(camera: RemoteCameraService = Depends(get_camera_service)):
    """Status połączenia z kamerą."""
    data = await camera.health_check()
    return CameraHealthResponse(
        status=HealthStatus(data.get("status", "error")),
        camera_url=data.get("camera_url", ""),
        response_code=data.get("response_code"),
        error=data.get("error"),
        has_cached_frame=data.get("has_cached_frame", False)
    )


# ============== EDGE DETECTION (placeholder) ==============

@edge_router.get("/detect")
async def detect_edge():
    """Detekcja krawędzi - coming soon."""
    return {"status": "not_implemented"}


# ============== RECORDING ==============

@recording_router.get("/status", response_model=RecordingStatusResponse)
async def recording_status(
    overlay_svc: FrameOverlayService = Depends(get_overlay_service),
    recorder: VideoRecorderService = Depends(get_recorder_service)
):
    """Status nagrywania."""
    return RecordingStatusResponse(
        is_recording=overlay_svc.is_recording,
        duration_seconds=overlay_svc.get_recording_duration(),
        frames=recorder.frame_count if recorder.is_recording else 0
    )


@recording_router.post("/start", response_model=RecordingStartResponse)
async def start_recording(
    overlay_svc: FrameOverlayService = Depends(get_overlay_service),
    recorder: VideoRecorderService = Depends(get_recorder_service)
):
    """Rozpocznij nagrywanie."""
    if overlay_svc.is_recording:
        raise HTTPException(400, "Nagrywanie już aktywne")
    
    filename = recorder.start()
    overlay_svc.start_recording()
    return RecordingStartResponse(status="started", filename=filename)


@recording_router.post("/stop", response_model=RecordingStopResponse)
async def stop_recording(
    overlay_svc: FrameOverlayService = Depends(get_overlay_service),
    recorder: VideoRecorderService = Depends(get_recorder_service)
):
    """Zatrzymaj nagrywanie."""
    if not overlay_svc.is_recording:
        raise HTTPException(400, "Nagrywanie nie jest aktywne")
    
    result = recorder.stop()
    overlay_svc.stop_recording()
    return RecordingStopResponse(status="stopped", **result)


@recording_router.get("/list", response_model=RecordingListResponse)
async def list_recordings(recorder: VideoRecorderService = Depends(get_recorder_service)):
    """Lista nagrań."""
    return RecordingListResponse(recordings=recorder.list_files())


@recording_router.get("/download/{filename}")
async def download_recording(
    filename: str,
    recorder: VideoRecorderService = Depends(get_recorder_service)
):
    """Pobierz nagranie na komputer."""
    path = recorder.get_path(filename)
    if not path:
        raise HTTPException(404, "Plik nie istnieje")
    return FileResponse(path, filename=filename, media_type="video/mp4")


@recording_router.delete("/{filename}")
async def delete_recording(
    filename: str,
    recorder: VideoRecorderService = Depends(get_recorder_service)
):
    """Usuń nagranie."""
    path = recorder.get_path(filename)
    if not path:
        raise HTTPException(404, "Plik nie istnieje")
    path.unlink()
    return {"status": "deleted", "filename": filename}
