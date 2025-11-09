"""
Remote Camera Service - Proxy do camera-server
Streamuje dane BEZPOŚREDNIO z camera-server bez dekodowania
"""
import httpx
from app.core.config import settings


class RemoteCameraService:
    """Serwis pobierający stream ze zdalnego camera-server przez HTTP"""
    
    def __init__(self):
        self.camera_server_url = settings.CAMERA_SERVER_URL
        self.stream_endpoint = f"{self.camera_server_url}/stream"
        self.health_endpoint = f"{self.camera_server_url}/health"
    
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
