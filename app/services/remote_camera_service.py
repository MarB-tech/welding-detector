"""Remote Camera Service - Proxy streamu MJPEG."""

import httpx
import asyncio
import logging
from typing import Optional, AsyncGenerator
from app.config import settings

logger = logging.getLogger(__name__)


class RemoteCameraService:
    """Proxy do streamu MJPEG z buforem klatek dla płynnego overlay."""
    
    def __init__(self):
        self.camera_url = settings.CAMERA_SERVER_URL
        self._client: Optional[httpx.AsyncClient] = None
        self._last_frame: Optional[bytes] = None
        self._frame_task: Optional[asyncio.Task] = None
        logger.info(f"📡 RemoteCameraService: {self.camera_url}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Reuse client dla lepszej wydajności."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._client
    
    async def get_single_frame(self) -> Optional[bytes]:
        """Pobiera pojedynczą klatkę z kamery."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.camera_url}/capture")
            if response.status_code == 200:
                return response.content
        except Exception as e:
            logger.warning(f"Frame error: {e}")
        return None
    
    async def stream_raw(self) -> AsyncGenerator[bytes, None]:
        """Bezpośredni proxy streamu - bez parsowania."""
        while True:
            try:
                client = await self._get_client()
                async with client.stream("GET", f"{self.camera_url}/stream") as response:
                    if response.status_code != 200:
                        continue
                    logger.info("📹 Stream connected")
                    async for chunk in response.aiter_raw():
                        yield chunk
            except Exception as e:
                logger.warning(f"Stream error: {e}")
    
    async def _frame_fetcher(self):
        """Tło - ciągle pobiera klatki do bufora."""
        while True:
            try:
                client = await self._get_client()
                async with client.stream("GET", f"{self.camera_url}/stream") as response:
                    if response.status_code != 200:
                        await asyncio.sleep(0.5)
                        continue
                    buffer = b""
                    async for chunk in response.aiter_raw():
                        buffer += chunk
                        while b'\xff\xd8' in buffer and b'\xff\xd9' in buffer:
                            start = buffer.find(b'\xff\xd8')
                            end = buffer.find(b'\xff\xd9', start) + 2
                            if start < end:
                                self._last_frame = buffer[start:end]
                                buffer = buffer[end:]
            except Exception as e:
                logger.warning(f"Frame fetcher error: {e}")
                await asyncio.sleep(0.5)
    
    def _ensure_frame_fetcher(self):
        """Upewnij się że fetcher działa."""
        if self._frame_task is None or self._frame_task.done():
            self._frame_task = asyncio.create_task(self._frame_fetcher())
    
    async def stream_frames(self, fps: int = 60) -> AsyncGenerator[bytes, None]:
        """Płynny stream klatek z bufora - stałe FPS, bez zacinania."""
        self._ensure_frame_fetcher()
        interval = 1.0 / fps
        
        while True:
            if self._last_frame:
                yield self._last_frame
            await asyncio.sleep(interval)
    
    async def health_check(self) -> dict:
        """Sprawdza połączenie z kamerą."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.camera_url}/capture")
            return {"status": "healthy" if response.status_code == 200 else "unhealthy",
                    "camera_url": self.camera_url, "response_code": response.status_code}
        except Exception as e:
            return {"status": "disconnected", "camera_url": self.camera_url, "error": str(e)}


_camera_service: Optional[RemoteCameraService] = None

def get_camera_service() -> RemoteCameraService:
    global _camera_service
    if _camera_service is None:
        _camera_service = RemoteCameraService()
    return _camera_service
