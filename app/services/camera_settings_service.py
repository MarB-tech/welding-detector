"""
Camera Settings Service - Proste zarządzanie ustawieniami kamery.
"""

import cv2  # type: ignore
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CameraSettingsService:
    """Serwis do zarządzania ustawieniami kamery."""
    
    def __init__(self, camera_service):
        """
        Args:
            camera_service: Instancja Camera_USB_Service
        """
        self.camera_service = camera_service
        logger.info("⚙️ CameraSettingsService initialized")
    
    # Dostępne rozdzielczości
    RESOLUTIONS = {
        "HD": (1280, 720),
        "FHD": (1920, 1080)
    }
    
    def apply_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Zastosuj ustawienia do kamery.
        
        Obsługiwane ustawienia:
        - contrast: 0-255
        - fps: 15, 30, 60
        - jpeg_quality: 50-100
        - resolution: "HD" lub "FHD"
        """
        if self.camera_service.cap is None or not self.camera_service.cap.isOpened():
            return {"error": "Kamera nie jest podłączona"}
        
        results = {}
        cap = self.camera_service.cap
        
        # Rozdzielczość
        if 'resolution' in settings:
            res_name = settings['resolution'].upper()
            if res_name in self.RESOLUTIONS:
                width, height = self.RESOLUTIONS[res_name]
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                results['resolution'] = {
                    "requested": res_name, 
                    "actual": f"{actual_w}x{actual_h}",
                    "success": actual_w == width and actual_h == height
                }
                logger.info(f"✅ resolution = {actual_w}x{actual_h}")
            else:
                results['resolution'] = {"error": f"Nieznana rozdzielczość: {res_name}"}
        
        # Kontrast
        if 'contrast' in settings:
            value = settings['contrast']
            success = cap.set(cv2.CAP_PROP_CONTRAST, value)
            actual = cap.get(cv2.CAP_PROP_CONTRAST)
            results['contrast'] = {"requested": value, "actual": actual, "success": success}
            logger.info(f"✅ contrast = {actual}")
        
        # FPS
        if 'fps' in settings:
            value = settings['fps']
            success = cap.set(cv2.CAP_PROP_FPS, value)
            actual = cap.get(cv2.CAP_PROP_FPS)
            results['fps'] = {"requested": value, "actual": actual, "success": success}
            logger.info(f"✅ fps = {actual}")
        
        # JPEG Quality (w camera_service, nie w OpenCV)
        if 'jpeg_quality' in settings:
            value = settings['jpeg_quality']
            self.camera_service.jpeg_quality = value
            results['jpeg_quality'] = {"requested": value, "actual": value, "success": True}
            logger.info(f"✅ jpeg_quality = {value}")
        
        return results
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Pobierz aktualne ustawienia kamery."""
        if self.camera_service.cap is None or not self.camera_service.cap.isOpened():
            return {"error": "Kamera nie jest podłączona"}
        
        cap = self.camera_service.cap
        
        # Określ nazwę rozdzielczości
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        resolution = "HD"  # domyślnie
        for name, (w, h) in self.RESOLUTIONS.items():
            if w == width and h == height:
                resolution = name
                break
        
        return {
            "contrast": cap.get(cv2.CAP_PROP_CONTRAST),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "jpeg_quality": self.camera_service.jpeg_quality,
            "resolution": resolution,
            "resolution_actual": f"{width}x{height}"
        }


# Singleton
_settings_service: Optional[CameraSettingsService] = None

def get_camera_settings_service() -> CameraSettingsService:
    global _settings_service
    if _settings_service is None:
        from app.services.remote_camera_service import get_camera_service
        camera_svc = get_camera_service()
        _settings_service = CameraSettingsService(camera_svc._camera)
    return _settings_service
