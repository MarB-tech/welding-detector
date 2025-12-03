"""
API Routes - Endpointy kamery i nagrywania.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response, FileResponse

from datetime import datetime

from app.services.remote_camera_service import RemoteCameraService, get_camera_service
from app.services.frame_overlay_service import FrameOverlayService, get_overlay_service
from app.services.video_recorder_service import VideoRecorderService, get_recorder_service
from app.services.video_overlay_service import VideoOverlayService, get_video_overlay_service
from app.services.camera_settings_service import CameraSettingsService, get_camera_settings_service
from app.api.models import (
    CameraHealthResponse, HealthStatus,
    RecordingStatusResponse, RecordingStartResponse, RecordingStopResponse, RecordingListResponse,
    CameraSettingsRequest
)

camera_router = APIRouter(prefix="/camera", tags=["Camera"])
edge_router = APIRouter(prefix="/edge", tags=["Edge Detection"])
recording_router = APIRouter(prefix="/recording", tags=["Recording"])


# ============== CAMERA ==============

@camera_router.get("/stream")
async def stream_camera(camera: RemoteCameraService = Depends(get_camera_service)):
    """Proxy MJPEG stream - minimalne opóźnienie."""
    headers = {"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"}
    return StreamingResponse(
        camera.stream_raw(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers=headers
    )


@camera_router.get("/stream/overlay")
async def stream_camera_overlay(
    camera: RemoteCameraService = Depends(get_camera_service),
    overlay_svc: FrameOverlayService = Depends(get_overlay_service)
):
    """Stream z live overlay (timestamp, REC indicator) - do podglądu."""
    async def generate():
        async for frame in camera.stream_frames():
            frame = overlay_svc.apply_overlay_to_jpeg(frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
    
    headers = {"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"}
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame", headers=headers)


@camera_router.get("/stream/recording")
async def stream_camera_recording(
    camera: RemoteCameraService = Depends(get_camera_service),
    overlay_svc: FrameOverlayService = Depends(get_overlay_service),
    recorder: VideoRecorderService = Depends(get_recorder_service)
):
    """Stream z nagrywaniem - overlay tylko na podgląd, nagranie czyste."""
    async def generate():
        async for frame in camera.stream_frames():
            # Nagrywamy CZYSTĄ klatkę (bez overlay)
            if recorder.is_recording:
                recorder.add_frame(frame)
            # Ale wyświetlamy z overlay (dla użytkownika)
            display_frame = overlay_svc.apply_overlay_to_jpeg(frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + display_frame + b'\r\n'
    
    headers = {"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"}
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame", headers=headers)


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
    """Status kamery USB."""
    data = await camera.health_check()
    return CameraHealthResponse(
        status=HealthStatus(data.get("status", "disconnected")),
        camera_index=data.get("camera_index"),
        fps=data.get("fps"),
        resolution=data.get("resolution"),
        error=data.get("error")
    )


@camera_router.get("/monochrome")
async def get_monochrome(camera: RemoteCameraService = Depends(get_camera_service)):
    """Pobierz status trybu monochromatycznego."""
    return {"monochrome": camera.monochrome}


@camera_router.post("/monochrome")
async def set_monochrome(
    enabled: bool = Query(..., description="Włącz/wyłącz tryb monochromatyczny"),
    camera: RemoteCameraService = Depends(get_camera_service)
):
    """Przełącz tryb monochromatyczny (grayscale)."""
    camera.monochrome = enabled
    return {"monochrome": camera.monochrome, "status": "ok"}


# ============== CAMERA SETTINGS ==============

@camera_router.get("/settings")
async def get_camera_settings(
    settings_svc: CameraSettingsService = Depends(get_camera_settings_service)
):
    """Pobierz aktualne ustawienia kamery (contrast, fps, jpeg_quality)."""
    return settings_svc.get_current_settings()


@camera_router.put("/settings")
async def update_camera_settings(
    request: CameraSettingsRequest,
    settings_svc: CameraSettingsService = Depends(get_camera_settings_service)
):
    """
    Zmień ustawienia kamery.
    
    Obsługiwane parametry:
    - contrast: 0-255
    - fps: 15, 30, 60
    - jpeg_quality: 50-100
    """
    return settings_svc.apply_settings(request.model_dump(exclude_none=True))


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


@recording_router.post("/{filename}/apply-overlay")
async def apply_overlay_to_recording(
    filename: str,
    start_time: str = None,
    recorder: VideoRecorderService = Depends(get_recorder_service),
    overlay_svc: VideoOverlayService = Depends(get_video_overlay_service)
):
    """
    Nakłada timestamp overlay na nagrane wideo (w tle).
    Tworzy nowy plik z sufiksem _overlay.
    """
    path = recorder.get_path(filename)
    if not path:
        raise HTTPException(404, "Plik nie istnieje")
    
    # Parse start_time jeśli podany
    parsed_time = None
    if start_time:
        try:
            parsed_time = datetime.fromisoformat(start_time)
        except ValueError:
            raise HTTPException(400, "Nieprawidłowy format start_time (użyj ISO 8601)")
    
    started = overlay_svc.process_video(filename, parsed_time)
    if not started:
        status = overlay_svc.get_status(filename)
        if status:
            return {"status": "already_processing", "details": status}
        raise HTTPException(500, "Nie można rozpocząć przetwarzania")
    
    return {
        "status": "processing_started",
        "filename": filename,
        "message": "Overlay będzie nałożony w tle. Sprawdź status przez GET /recording/{filename}/overlay-status"
    }


@recording_router.get("/{filename}/overlay-status")
async def get_overlay_status(
    filename: str,
    overlay_svc: VideoOverlayService = Depends(get_video_overlay_service)
):
    """Sprawdź status nakładania overlay na wideo."""
    status = overlay_svc.get_status(filename)
    if not status:
        return {"status": "not_found", "message": "Brak przetwarzania dla tego pliku"}
    return status


@recording_router.get("/overlay-jobs")
async def get_all_overlay_jobs(
    overlay_svc: VideoOverlayService = Depends(get_video_overlay_service)
):
    """Lista wszystkich zadań nakładania overlay."""
    return overlay_svc.get_all_status()
