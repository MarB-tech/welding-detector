"""
Testy produkcyjne dla Backend API
Uruchom: pytest tests/ -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app


@pytest.fixture
def mock_camera_service():
    """Mock dla RemoteCameraService"""
    with patch('app.api.routes.camera_service') as mock:
        yield mock


class TestRootEndpoint:
    """Testy dla głównego endpointu /"""
    
    @pytest.mark.asyncio
    async def test_root_returns_status_running(self):
        """Test: Endpoint / zwraca status 'running'"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_root_contains_camera_url(self):
        """Test: Endpoint / zawiera camera_url"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            data = response.json()
            
            assert "camera_url" in data
            assert isinstance(data["camera_url"], str)
            assert len(data["camera_url"]) > 0


class TestHealthEndpoint:
    """Testy dla /health - krytyczne dla monitoringu produkcyjnego"""
    
    @pytest.mark.asyncio
    async def test_health_check_when_camera_healthy(self, mock_camera_service):
        """Test: Health check zwraca healthy gdy camera-server działa"""
        mock_camera_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "camera_server": {"camera_ready": True, "camera_index": 1}
        })
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["api"] == "healthy"
            assert data["camera_service"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_when_camera_unreachable(self, mock_camera_service):
        """Test: Health check zwraca error gdy camera-server niedostępny"""
        mock_camera_service.health_check = AsyncMock(return_value={
            "status": "error",
            "message": "Cannot connect to camera-server"
        })
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            
            # API powinno odpowiedzieć 200 nawet jeśli camera-server nie działa
            assert response.status_code == 200
            data = response.json()
            assert data["api"] == "healthy"
            assert data["camera_service"]["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_health_response_time(self, mock_camera_service):
        """Test: Health check odpowiada szybko (< 500ms)"""
        import time
        
        mock_camera_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "camera_server": {}
        })
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start = time.time()
            response = await client.get("/health")
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration < 0.5  # Maksymalnie 500ms


class TestStreamEndpoint:
    """Testy dla /stream - główna funkcjonalność"""
    
    @pytest.mark.asyncio
    async def test_stream_returns_correct_content_type(self, mock_camera_service):
        """Test: Stream zwraca poprawny content-type dla MJPEG"""
        async def mock_stream():
            yield b'--frame\r\n'
            yield b'Content-Type: image/jpeg\r\n\r\n'
            yield b'fake_jpeg_data\r\n'
        
        mock_camera_service.get_stream = mock_stream
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/stream")
            
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert "multipart/x-mixed-replace" in content_type
            assert "boundary=frame" in content_type
    
    @pytest.mark.asyncio
    async def test_stream_yields_data(self, mock_camera_service):
        """Test: Stream faktycznie zwraca dane"""
        async def mock_stream():
            for i in range(3):
                yield f'frame_{i}\r\n'.encode()
        
        mock_camera_service.get_stream = mock_stream
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with client.stream("GET", "/stream") as response:
                assert response.status_code == 200
                
                chunks = []
                async for chunk in response.aiter_bytes():
                    chunks.append(chunk)
                
                # StreamingResponse może buforować, więc sprawdzamy czy otrzymaliśmy JAKIEKOLWIEK dane
                assert len(chunks) >= 1
                # I czy zawierają nasze frame'y
                all_data = b''.join(chunks)
                assert b'frame_0' in all_data
                assert b'frame_1' in all_data
                assert b'frame_2' in all_data
    
    @pytest.mark.asyncio
    async def test_stream_handles_empty_response(self, mock_camera_service):
        """Test: Stream obsługuje przypadek braku danych"""
        async def mock_empty_stream():
            yield b''
        
        mock_camera_service.get_stream = mock_empty_stream
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/stream")
            assert response.status_code == 200


class TestAPIDocumentation:
    """Testy dla dokumentacji API (Swagger/OpenAPI)"""
    
    @pytest.mark.asyncio
    async def test_openapi_json_exists(self):
        """Test: OpenAPI schema jest dostępny"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/openapi.json")
            
            assert response.status_code == 200
            schema = response.json()
            assert "openapi" in schema
            assert "paths" in schema
    
    @pytest.mark.asyncio
    async def test_openapi_contains_required_endpoints(self):
        """Test: OpenAPI zawiera wszystkie wymagane endpointy"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/openapi.json")
            schema = response.json()
            
            paths = schema["paths"]
            assert "/" in paths
            assert "/health" in paths
            assert "/stream" in paths
    
    @pytest.mark.asyncio
    async def test_swagger_ui_accessible(self):
        """Test: Swagger UI jest dostępny"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/docs")
            
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")


class TestErrorHandling:
    """Testy obsługi błędów"""
    
    @pytest.mark.asyncio
    async def test_404_for_non_existent_endpoint(self):
        """Test: API zwraca 404 dla nieistniejących endpointów"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/non-existent-endpoint")
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_cors_headers_if_enabled(self):
        """Test: CORS headers (jeśli są skonfigurowane)"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            
            # Ten test może wymagać konfiguracji CORS w aplikacji
            # Obecnie sprawdzamy tylko czy endpoint działa
            assert response.status_code == 200


class TestProduction:
    """Testy specyficzne dla środowiska produkcyjnego"""
    
    @pytest.mark.asyncio
    async def test_api_responds_under_load(self, mock_camera_service):
        """Test: API odpowiada przy wielokrotnych requestach"""
        mock_camera_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "camera_server": {}
        })
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Symuluj 10 równoczesnych requestów
            tasks = []
            for _ in range(10):
                tasks.append(client.get("/health"))
            
            # Wszystkie powinny zakończyć się sukcesem
            responses = await asyncio.gather(*tasks)
            for response in responses:
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_app_title_is_set(self):
        """Test: Aplikacja ma ustawiony tytuł"""
        assert app.title == "Welding Vision API"


# Import asyncio dla testów współbieżności
import asyncio
