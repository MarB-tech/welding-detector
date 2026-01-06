"""API Routes - Camera, Recording, Edge Detection."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response, FileResponse
from datetime import datetime
from typing import Optional
from pathlib import Path

from app.services.camera_service import CameraService, get_camera_service
from app.services.frame_overlay_service import FrameOverlayService, get_overlay_service
from app.services.video_overlay_service import VideoOverlayService, get_video_overlay_service
from app.services.frame_extractor_service import FrameExtractorService, get_frame_extractor_service
from app.services.motion_detection_service import MotionDetectionService, get_motion_detection_service
from app.api.models import (
    CameraHealthResponse, HealthStatus,
    RecordingStatusResponse, RecordingStartResponse, RecordingStopResponse, RecordingListResponse,
    CameraSettingsRequest,
    VideoInfoResponse, ExtractFramesRequest, ExtractFramesResponse, FrameResponse,
    MotionAnalysisResponse, MotionSegmentResponse, TrimToMotionRequest, TrimToMotionResponse
)

camera_router = APIRouter(prefix="/camera", tags=["Camera"])
edge_router = APIRouter(prefix="/edge", tags=["Edge Detection"])
recording_router = APIRouter(prefix="/recording", tags=["Recording"])


# ============== CAMERA ==============

@camera_router.get("/stream")
async def stream_camera(camera: CameraService = Depends(get_camera_service)):
    return StreamingResponse(camera.stream_raw(), media_type="multipart/x-mixed-replace; boundary=frame",
                            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@camera_router.get("/stream/overlay")
async def stream_camera_overlay(camera: CameraService = Depends(get_camera_service), overlay: FrameOverlayService = Depends(get_overlay_service)):
    async def gen():
        async for frame in camera.stream_frames():
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + overlay.apply_overlay_to_jpeg(frame) + b'\r\n'
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")


@camera_router.get("/capture")
async def capture_frame(overlay: bool = True, camera: CameraService = Depends(get_camera_service), overlay_svc: FrameOverlayService = Depends(get_overlay_service)):
    frame = await camera.get_single_frame()
    if not frame:
        raise HTTPException(503, "Camera unavailable")
    return Response(overlay_svc.apply_overlay_to_jpeg(frame) if overlay else frame, media_type="image/jpeg")


@camera_router.get("/health", response_model=CameraHealthResponse)
async def camera_health(camera: CameraService = Depends(get_camera_service)):
    data = await camera.health_check()
    return CameraHealthResponse(status=HealthStatus(data.get("status", "disconnected")), **{k: data.get(k) for k in ["camera_index", "fps", "resolution", "is_recording"]})


@camera_router.get("/monochrome")
async def get_monochrome(camera: CameraService = Depends(get_camera_service)):
    return {"monochrome": camera.monochrome}


@camera_router.post("/monochrome")
async def set_monochrome(enabled: bool = Query(...), camera: CameraService = Depends(get_camera_service)):
    camera.monochrome = enabled
    return {"monochrome": camera.monochrome}


@camera_router.get("/settings")
async def get_settings(camera: CameraService = Depends(get_camera_service)):
    return camera.get_settings()


@camera_router.put("/settings")
async def update_settings(req: CameraSettingsRequest, camera: CameraService = Depends(get_camera_service)):
    return camera.apply_settings(**req.model_dump(exclude_none=True))


# ============== EDGE ==============

@edge_router.get("/detect")
async def detect_edge():
    return {"status": "not_implemented"}


# ============== RECORDING ==============

@recording_router.get("/status", response_model=RecordingStatusResponse)
async def recording_status(camera: CameraService = Depends(get_camera_service)):
    return RecordingStatusResponse(is_recording=camera.is_recording, duration_seconds=camera.get_recording_duration(), frames=camera._frame_count)


@recording_router.post("/start", response_model=RecordingStartResponse)
async def start_recording(camera: CameraService = Depends(get_camera_service), overlay: FrameOverlayService = Depends(get_overlay_service)):
    if camera.is_recording:
        raise HTTPException(400, "Already recording")
    overlay.start_recording()
    return RecordingStartResponse(status="started", filename=camera.start_recording())


@recording_router.post("/stop", response_model=RecordingStopResponse)
async def stop_recording(camera: CameraService = Depends(get_camera_service), overlay: FrameOverlayService = Depends(get_overlay_service)):
    if not camera.is_recording:
        raise HTTPException(400, "Not recording")
    overlay.stop_recording()
    return RecordingStopResponse(status="stopped", **camera.stop_recording())


@recording_router.get("/list", response_model=RecordingListResponse)
async def list_recordings(camera: CameraService = Depends(get_camera_service)):
    return RecordingListResponse(recordings=camera.list_recordings())


@recording_router.get("/download/{filename}")
async def download_recording(filename: str, camera: CameraService = Depends(get_camera_service)):
    path = camera.get_recording_path(filename)
    if not path:
        raise HTTPException(404, "File not found")
    return FileResponse(path, filename=filename, media_type="video/mp4")


@recording_router.delete("/{filename}")
async def delete_recording(filename: str, camera: CameraService = Depends(get_camera_service)):
    if not camera.delete_recording(filename):
        raise HTTPException(404, "File not found")
    return {"status": "deleted", "filename": filename}


@recording_router.put("/{filename}/note")
async def set_recording_note(filename: str, note: str = Query("", max_length=500), camera: CameraService = Depends(get_camera_service)):
    if not camera.set_note(filename, note):
        raise HTTPException(404, "File not found")
    return {"status": "saved", "filename": filename, "note": note}

@recording_router.post("/{filename}/apply-overlay")
async def apply_overlay(filename: str, start_time: Optional[str] = None, camera: CameraService = Depends(get_camera_service), overlay: VideoOverlayService = Depends(get_video_overlay_service)):
    if not camera.get_recording_path(filename):
        raise HTTPException(404, "File not found")
    parsed_time = datetime.fromisoformat(start_time) if start_time else None
    if not overlay.process_video(filename, parsed_time):
        return {"status": "already_processing"}
    return {"status": "processing_started", "filename": filename}


@recording_router.get("/{filename}/overlay-status")
async def overlay_status(filename: str, overlay: VideoOverlayService = Depends(get_video_overlay_service)):
    return overlay.get_status(filename) or {"status": "not_found"}


# ============== FRAME EXTRACTION ==============

@recording_router.get("/{filename}/info", response_model=VideoInfoResponse)
async def get_video_info(
    filename: str,
    camera: CameraService = Depends(get_camera_service),
    extractor: FrameExtractorService = Depends(get_frame_extractor_service)
):
    """Pobiera informacje o pliku wideo (liczba klatek, fps, rozdzielczość)."""
    path = camera.get_recording_path(filename)
    if not path:
        raise HTTPException(404, "File not found")
    
    try:
        info = extractor.get_video_info(path)
        return VideoInfoResponse(filename=filename, **info)
    except Exception as e:
        raise HTTPException(500, f"Cannot read video info: {e}")


@recording_router.post("/{filename}/extract-frames", response_model=ExtractFramesResponse)
async def extract_frames(
    filename: str,
    req: ExtractFramesRequest,
    camera: CameraService = Depends(get_camera_service),
    extractor: FrameExtractorService = Depends(get_frame_extractor_service)
):
    """
    Ekstrahuje klatki z nagrania i zapisuje jako JPEG.
    
    - step: co która klatka (1 = każda, 2 = co druga, itd.)
    - max_frames: limit klatek do wyekstrahowania
    - output_folder: folder docelowy (domyślnie: frames/{filename}/)
    """
    path = camera.get_recording_path(filename)
    if not path:
        raise HTTPException(404, "File not found")
    
    # Ustal folder docelowy
    base_name = Path(filename).stem
    output_folder = req.output_folder or f"frames/{base_name}"
    
    try:
        frames = extractor.extract_frames(path, step=req.step, max_frames=req.max_frames)
        saved = extractor.save_frames_to_folder(
            frames, 
            output_folder, 
            prefix=req.prefix,
            jpeg_quality=req.jpeg_quality
        )
        
        return ExtractFramesResponse(
            status="completed",
            filename=filename,
            frames_extracted=len(frames),
            output_folder=output_folder,
            files=[f.name for f in saved]
        )
    except Exception as e:
        raise HTTPException(500, f"Extraction failed: {e}")


@recording_router.get("/{filename}/frame/{frame_index}")
async def get_single_frame(
    filename: str,
    frame_index: int,
    camera: CameraService = Depends(get_camera_service),
    extractor: FrameExtractorService = Depends(get_frame_extractor_service)
):
    """
    Pobiera pojedynczą klatkę z nagrania jako JPEG.
    
    - frame_index: numer klatki (0-based)
    """
    path = camera.get_recording_path(filename)
    if not path:
        raise HTTPException(404, "File not found")
    
    try:
        # Użyj generatora aby nie ładować wszystkich klatek
        import cv2
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise HTTPException(500, "Cannot open video file")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_index < 0 or frame_index >= total_frames:
            cap.release()
            raise HTTPException(400, f"Frame index out of range (0-{total_frames-1})")
        
        # Przeskocz do żądanej klatki
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise HTTPException(500, "Cannot read frame")
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return Response(buffer.tobytes(), media_type="image/jpeg")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get frame: {e}")


# ============== MOTION DETECTION ==============

@recording_router.get("/{filename}/detect-motion", response_model=MotionAnalysisResponse)
async def detect_motion(
    filename: str,
    threshold: int = 25,
    min_area_percent: float = 0.5,
    camera: CameraService = Depends(get_camera_service),
    motion: MotionDetectionService = Depends(get_motion_detection_service)
):
    """
    Analizuje nagranie i wykrywa segmenty z ruchem kamery/obiektu.
    
    - threshold: próg różnicy pikseli (0-255), wyższy = mniej czuły
    - min_area_percent: minimalny % powierzchni ze zmianą
    """
    path = camera.get_recording_path(filename)
    if not path:
        raise HTTPException(404, "File not found")
    
    try:
        result = motion.detect_motion(path, threshold=threshold, min_area_percent=min_area_percent)
        return MotionAnalysisResponse(
            filename=result.filename,
            total_frames=result.total_frames,
            fps=result.fps,
            duration_seconds=result.duration_seconds,
            segments=[MotionSegmentResponse(
                start_frame=s.start_frame,
                end_frame=s.end_frame,
                start_time_ms=s.start_time_ms,
                end_time_ms=s.end_time_ms,
                duration_ms=s.duration_ms
            ) for s in result.segments],
            motion_percentage=result.motion_percentage
        )
    except Exception as e:
        raise HTTPException(500, f"Motion detection failed: {e}")


@recording_router.post("/{filename}/trim-to-motion", response_model=TrimToMotionResponse)
async def trim_to_motion(
    filename: str,
    req: TrimToMotionRequest,
    camera: CameraService = Depends(get_camera_service),
    motion: MotionDetectionService = Depends(get_motion_detection_service)
):
    """
    Przycina nagranie do segmentów z wykrytym ruchem.
    
    Tworzy nowy plik zawierający tylko fragmenty z ruchem kamery.
    """
    path = camera.get_recording_path(filename)
    if not path:
        raise HTTPException(404, "File not found")
    
    # Ustal ścieżkę wyjściową
    output_path = None
    if req.output_filename:
        output_path = path.parent / req.output_filename
    
    try:
        result = motion.trim_to_motion(
            path,
            output_path=output_path,
            threshold=req.threshold,
            min_area_percent=req.min_area_percent,
            include_all_segments=req.include_all_segments
        )
        return TrimToMotionResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"Trim failed: {e}")

