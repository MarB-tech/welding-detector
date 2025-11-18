from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from app.core.config import settings
import httpx
from app.services.remote_camera_service import RemoteCameraService
from app.services.image_processing_service import ImageProcessingService
from app.services.video_recorder_service import VideoRecorder


router = APIRouter()
camera_service = RemoteCameraService()
image_processing = ImageProcessingService()
video_recorder = VideoRecorder()

@router.get("/stream", tags=["Camera"])
async def stream():
    """
    MJPEG video stream z kamery
    
    Ciągły strumień wideo w formacie MJPEG.
    Proxy do camera-server - przekazuje bajty bez przetwarzania.
    """
    return StreamingResponse(
        camera_service.get_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/capture", tags=["Camera"])
async def capture():
    """
    Pojedyncza klatka z kamery jako JPEG
    
    Pobiera PIERWSZĄ klatkę ze strumienia MJPEG i zwraca jako obraz JPEG.
    
    **Działa w Dockerze!** Nie wymaga opencv-python.
    
    **Użycie:**
    - Przeglądarka: `http://localhost:8000/capture`
    - Python: `requests.get('http://localhost:8000/capture').content`
    - PowerShell: `Invoke-WebRequest -Uri http://localhost:8000/capture -OutFile foto.jpg`
    - cURL: `curl http://localhost:8000/capture -o foto.jpg`
    
    **Response:**
    - 200 OK: Zwraca obraz JPEG
    - 503 Service Unavailable: Kamera niedostępna lub błąd streamu
    
    **Jak to działa:**
    1. Łączy się ze streamem MJPEG z camera-server
    2. Parsuje strumień i wyciąga pierwszą kompletną klatkę JPEG
    3. Zwraca surowe bajty JPEG
    """
    frame = await camera_service.capture_frame_from_stream()
    
    if frame:
        return Response(
            content=frame,
            media_type="image/jpeg",
            headers={
                "Content-Length": str(len(frame)),
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    else:
        return Response(
            content=b"Camera unavailable or stream error",
            status_code=503,
            media_type="text/plain"
        )

@router.get("/health", tags=["Camera"])
async def health():
    """
    Health check - prosty status dla monitoringu
    
    Używane przez: Docker healthcheck, Kubernetes, monitoring tools.
    Szybka odpowiedź: czy system działa?
    """
    is_healthy = camera_service.is_healthy()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


@router.get("/stats", tags=["Camera"])
async def stats():
    """
    Szczegółowe statystyki kamery - dla admina i debugowania
    
    Zwraca pełne informacje: FPS, resolution, failures, recording status, etc.
    Używane przez: admin dashboard, debugging, analiza wydajności.
    """
    return camera_service.get_stats()


@router.get("/detect-edges", tags=["Image Processing"])
async def detect_edges(threshold1: int = 50, threshold2: int = 150):
    """
    Prosta detekcja krawędzi - zwraca obraz z wykrytymi krawędziami
    
    **Parametry:**
    - `threshold1` (int): Dolny próg Canny (default: 50)
    - `threshold2` (int): Górny próg Canny (default: 150)
    
    **Użycie:**
    ```
    GET /detect-edges?threshold1=30&threshold2=100
    ```
    
    **Response:**
    Obraz JPEG z zaznaczonymi krawędziami (biały = krawędź, czarny = tło)
    
    **Dostrajanie:**
    - Niższe thresholdy = więcej krawędzi (może być szum)
    - Wyższe thresholdy = mniej krawędzi (tylko silne kontrasty)
    """
    # Pobierz klatkę
    frame = await camera_service.capture_frame_from_stream()
    
    if not frame:
        return Response(
            content=b"Camera unavailable",
            status_code=503,
            media_type="text/plain"
        )
    
    # Wykryj krawędzie
    edges_image = image_processing.detect_edges_simple(frame, threshold1, threshold2)
    
    if edges_image:
        return Response(
            content=edges_image,
            media_type="image/jpeg",
            headers={
                "Content-Length": str(len(edges_image)),
                "Cache-Control": "no-cache"
            }
        )
    else:
        return Response(
            content=b"Edge detection failed",
            status_code=500,
            media_type="text/plain"
        )

    
@router.post("/start_recording", tags=["Recording"])
def start_recording():
    camera_service.start_recording()
    # video_recorder.start()
    return {"status": "recording started"}

@router.post("/stop_recording", tags=["Recording"])
def stop_recording():
    camera_service.stop_recording()
    # video_recorder.stop()
    return {"status": "recording stopped"}

# app/api/routes.py
@router.post("/recording/start")
async def start_recording():
    """Proxy do camera-server."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{settings.CAMERA_SERVER_URL}/recording/start")
        return response.json()