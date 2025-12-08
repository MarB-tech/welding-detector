"""Camera Service - Bezpośredni dostęp do kamery USB."""

import asyncio
import logging
import cv2  # type: ignore
import numpy as np
from typing import Optional, AsyncGenerator
from camera_server.camera_USB_service import Camera_USB_Service
from app.config import settings

logger = logging.getLogger(__name__)


class RemoteCameraService:
    """Bezpośredni dostęp do kamery USB (GStreamer)."""
    
    def __init__(self):
        self._camera = Camera_USB_Service(settings.CAMERA_INDEX)
        self._monochrome = False
        logger.info(f"📹 CameraService: index {settings.CAMERA_INDEX}")
    
    @property
    def monochrome(self) -> bool:
        return self._monochrome
    
    @monochrome.setter
    def monochrome(self, value: bool):
        self._monochrome = value
        logger.info(f"🎨 Monochrome: {'ON' if value else 'OFF'}")
    
    def _apply_monochrome(self, jpeg_bytes: bytes) -> bytes:
        if not self._monochrome:
            return jpeg_bytes
        try:
            frame = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return jpeg_bytes
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, buffer = cv2.imencode('.jpg', gray, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return buffer.tobytes()
        except Exception:
            return jpeg_bytes
    
    async def get_single_frame(self) -> Optional[bytes]:
        frame = self._camera.get_frame()
        return self._apply_monochrome(frame) if frame else None
    
    async def stream_raw(self) -> AsyncGenerator[bytes, None]:
        while True:
            frame = self._camera.get_frame()
            if frame:
                frame = self._apply_monochrome(frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n'
                       + frame + b'\r\n')
            await asyncio.sleep(1.0 / settings.CAMERA_USB_FPS)
    
    async def stream_frames(self, fps: int = settings.CAMERA_USB_FPS) -> AsyncGenerator[bytes, None]:
        interval = 1.0 / fps
        while True:
            frame = self._camera.get_frame()
            if frame:
                yield self._apply_monochrome(frame)
            await asyncio.sleep(interval)
    
    async def health_check(self) -> dict:
        stats = self._camera.get_stats()
        return {
            "status": "healthy" if stats.get("is_opened") else "disconnected",
            "camera_index": stats.get("camera_index"),
            "fps": stats.get("fps"),
            "resolution": f"{stats.get('width')}x{stats.get('height')}",
            "monochrome": self._monochrome
        }


_camera_service: Optional[RemoteCameraService] = None

def get_camera_service() -> RemoteCameraService:
    global _camera_service
    if _camera_service is None:
        _camera_service = RemoteCameraService()
    return _camera_service
