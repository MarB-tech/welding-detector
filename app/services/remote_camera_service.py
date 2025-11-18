"""
Remote Camera Service - Proxy do camera-server z pełną funkcjonalnością USB Camera
Dziedziczy po Camera_USB_Service i dodaje zdalne możliwości
"""
import httpx
from app.core.config import settings
from app.services.camera_USB_service import Camera_USB_Service


class RemoteCameraService(Camera_USB_Service):
    """
    Serwis proxy do zdalnej kamery - dziedziczy wszystkie funkcje Camera_USB_Service.
    
    Cechy dziedziczone:
    - Thread-safety
    - Auto-reconnection
    - Retry logic
    - Frame caching
    - Timestamp overlay
    - Recording indicator
    - get_stats(), is_healthy(), start_recording(), stop_recording()
    
    Dodatkowe cechy:
    - Proxy do camera-server przez HTTP
    - get_stream() - streaming MJPEG
    - capture_frame_from_stream() - pojedyncza klatka przez HTTP
    - health_check() - sprawdzanie zdalnego serwera
    """
    
    def __init__(self):
        """Initialize remote camera service - używa parent init bez hardware."""
        # ✅ Elegancko: wywołaj parent __init__ z camera_index=None (remote mode)
        self._remote_mode = True  # Flag dla parent class
        super().__init__(camera_index=None)
        
        # Dodaj tylko remote-specific attributes
        self.camera_server_url = settings.CAMERA_SERVER_URL
        self.stream_endpoint = f"{self.camera_server_url}/stream"
        self.health_endpoint = f"{self.camera_server_url}/health"
        self.capture_endpoint = f"{self.camera_server_url}/capture"
    
    def get_frame(self) -> bytes:
        """
        Override: pobiera klatkę przez HTTP z camera-server zamiast z USB.
        Zachowuje caching i error handling z parent class.
        
        Returns:
            bytes: JPEG frame z camera-server
        """
        import asyncio
        try:
            # Użyj asyncio do wywołania async metody
            frame = asyncio.run(self._fetch_frame_http())
            
            if frame:
                self.last_frame = frame
                self.consecutive_failures = 0
                return frame
            else:
                self.consecutive_failures += 1
                return self.last_frame if self.last_frame else b''
                
        except Exception as e:
            self.consecutive_failures += 1
            print(f"❌ Error getting frame: {e}")
            return self.last_frame if self.last_frame else b''
    
    async def _fetch_frame_http(self) -> bytes:
        """Fetch single frame from camera-server /capture endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.capture_endpoint)
                if response.status_code == 200:
                    return response.content
                return b''
        except Exception:
            return b''
    
    def is_healthy(self) -> bool:
        """
        Override: sprawdza health przez HTTP zamiast sprawdzania VideoCapture.
        """
        import asyncio
        try:
            result = asyncio.run(self.health_check())
            return result.get("status") == "healthy"
        except Exception:
            return False
    
    def get_stats(self) -> dict:
        """
        Override: zwraca stats z camera-server + własne info.
        """
        import asyncio
        stats = {
            "camera_type": "remote",
            "camera_server_url": self.camera_server_url,
            "consecutive_failures": self.consecutive_failures,
            "has_cached_frame": self.last_frame is not None,
            "is_healthy": self.is_healthy(),
            "is_recording": self.is_recording
        }
        
        # Dodaj stats z remote server
        try:
            remote_health = asyncio.run(self.health_check())
            if "camera_server" in remote_health:
                stats["remote_stats"] = remote_health["camera_server"]
        except Exception:
            pass
        
        return stats
    
    # === Metody specyficzne dla Remote (nie ma w USB) ===
    
    async def get_stream(self):
        """
        Pobiera stream z camera-server i przekazuje dalej jako PROXY.
        NIE dekoduje ani nie przetwarza obrazu - tylko przekazuje bajty.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream('GET', self.stream_endpoint) as response:
                    if response.status_code != 200:
                        print(f"❌ Camera server błąd: {response.status_code}")
                        yield b''
                        return
                    
                    print(f"✅ Połączono z camera-server: {self.stream_endpoint}")
                    
                    # Streamuj bajty bezpośrednio bez przetwarzania
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        yield chunk
                        
        except httpx.ConnectError as e:
            print(f"❌ Nie można połączyć się z camera-server: {e}")
            print(f"   Sprawdź czy camera-server działa na: {self.camera_server_url}")
            yield b''
        except Exception as e:
            print(f"❌ Błąd streamowania: {e}")
            yield b''
    
    async def health_check(self) -> dict:
        """Sprawdza status camera-server"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.health_endpoint)
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "camera_server": response.json()
                    }
                return {
                    "status": "unhealthy",
                    "code": response.status_code
                }
        except httpx.ConnectError:
            return {
                "status": "error",
                "message": f"Cannot connect to camera-server at {self.camera_server_url}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def capture_frame_from_stream(self) -> bytes:
        """
        Wyciąga pojedynczą klatkę JPEG ze strumienia MJPEG.
        
        Działa w Dockerze! Nie wymaga opencv-python.
        Parsuje strumień MJPEG i wyciąga pierwszą kompletną klatkę JPEG.
        
        Returns:
            bytes: Surowe dane JPEG obrazu lub b'' w przypadku błędu
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                async with client.stream('GET', self.stream_endpoint) as response:
                    if response.status_code != 200:
                        print(f"❌ Camera server błąd: {response.status_code}")
                        return b''
                    
                    print(f"✅ Pobieranie klatki ze strumienia: {self.stream_endpoint}")
                    
                    # Bufor na dane
                    buffer = b''
                    jpeg_data = b''
                    in_jpeg = False
                    
                    # Czytaj strumień chunk po chunk
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        buffer += chunk
                        
                        # Szukaj początku JPEG (FF D8)
                        if not in_jpeg:
                            jpeg_start = buffer.find(b'\xff\xd8')
                            if jpeg_start != -1:
                                in_jpeg = True
                                buffer = buffer[jpeg_start:]  # Odetnij wszystko przed JPEG
                                jpeg_data = buffer
                        else:
                            jpeg_data += chunk
                        
                        # Szukaj końca JPEG (FF D9)
                        if in_jpeg:
                            jpeg_end = jpeg_data.find(b'\xff\xd9')
                            if jpeg_end != -1:
                                # Znaleziono kompletny JPEG!
                                jpeg_frame = jpeg_data[:jpeg_end + 2]  # +2 dla FF D9
                                print(f"✅ Pobrano klatkę: {len(jpeg_frame)} bytes")
                                return jpeg_frame
                        
                        # Bezpieczeństwo: jeśli bufor przekroczy 5MB, coś jest nie tak
                        if len(jpeg_data) > 5 * 1024 * 1024:
                            print("❌ Przekroczono maksymalny rozmiar bufora")
                            return b''
                    
                    # Jeśli dotarliśmy tu, stream się zakończył bez kompletnej klatki
                    print("❌ Stream zakończył się przed znalezieniem klatki")
                    return b''
                    
        except httpx.ConnectError as e:
            print(f"❌ Nie można połączyć się z camera-server: {e}")
            return b''
        except Exception as e:
            print(f"❌ Błąd pobierania klatki: {e}")
            return b''

