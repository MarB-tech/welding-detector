"""
Testy integracyjne - symulują rzeczywiste scenariusze produkcyjne
UWAGA: Te testy wymagają działającego camera-server!
Uruchom: pytest tests/test_integration.py -v --run-integration
"""
import pytest
import httpx
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


# Marker dla testów integracyjnych
pytestmark = pytest.mark.integration


class TestRealCameraServerIntegration:
    """
    Testy integracyjne z prawdziwym camera-server
    Wymagają: camera-server działający na localhost:8001
    """
    
    @pytest.mark.asyncio
    async def test_backend_connects_to_real_camera_server(self, request):
        """Test: Backend łączy się z prawdziwym camera-server"""
        # Ten test wymaga działającego camera-server
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8001/health")
                assert response.status_code == 200
                print("✅ Camera-server jest dostępny")
        except httpx.ConnectError:
            pytest.skip("Camera-server nie działa na localhost:8001")
    
    @pytest.mark.asyncio
    async def test_full_stream_flow(self, request):
        """Test: Pełny przepływ streamu od camera-server przez backend"""
        try:
            # Sprawdź czy camera-server działa
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get("http://localhost:8001/health")
        except httpx.ConnectError:
            pytest.skip("Camera-server nie działa")
        
        # Test backend API
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with client.stream("GET", "/stream", timeout=10.0) as response:
                assert response.status_code == 200
                
                # Pobierz pierwsze kilka chunków
                chunks = []
                async for chunk in response.aiter_bytes():
                    chunks.append(chunk)
                    if len(chunks) >= 5:
                        break
                
                assert len(chunks) > 0
                print(f"✅ Otrzymano {len(chunks)} chunków danych")


class TestEndToEndScenarios:
    """Testy end-to-end dla typowych scenariuszy produkcyjnych"""
    
    @pytest.mark.asyncio
    async def test_health_check_monitoring_scenario(self):
        """
        Scenariusz: System monitorujący sprawdza health co 30s
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Symuluj 5 kolejnych health check'ów
            for i in range(5):
                response = await client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert "api" in data
                assert "camera_service" in data
                
                # Symuluj opóźnienie między sprawdzeniami
                await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_concurrent_stream_viewers_scenario(self):
        """
        Scenariusz: Wielu użytkowników ogląda stream jednocześnie
        """
        from unittest.mock import AsyncMock, patch
        
        # Mock camera service
        async def mock_stream():
            for i in range(3):
                yield f'frame_{i}'.encode()
        
        with patch('app.api.routes.camera_service') as mock:
            mock.get_stream = mock_stream
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Symuluj 3 równoczesnych viewerów
                async def get_stream():
                    async with client.stream("GET", "/stream") as response:
                        chunks = []
                        async for chunk in response.aiter_bytes():
                            chunks.append(chunk)
                            if len(chunks) >= 2:
                                break
                        return chunks
                
                results = await asyncio.gather(*[get_stream() for _ in range(3)])
                
                # Wszyscy viewers powinni otrzymać dane
                for chunks in results:
                    assert len(chunks) >= 2
    
    @pytest.mark.asyncio
    async def test_api_restart_recovery_scenario(self):
        """
        Scenariusz: API zostaje zrestartowane podczas działania
        """
        transport = ASGITransport(app=app)
        
        # Request przed "restartem"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response1 = await client.get("/health")
            assert response1.status_code == 200
        
        # Symuluj restart (nowy client)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response2 = await client.get("/health")
            assert response2.status_code == 200
            
            # API powinno działać normalnie
            assert response2.json()["api"] == "healthy"


class TestLoadAndStress:
    """Testy obciążeniowe - sprawdzają wydajność"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_api_handles_burst_traffic(self):
        """Test: API radzi sobie z nagłym wzrostem ruchu"""
        from unittest.mock import AsyncMock, patch
        
        mock_health = AsyncMock(return_value={"status": "healthy"})
        
        with patch('app.api.routes.camera_service') as mock:
            mock.health_check = mock_health
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # 20 równoczesnych requestów
                tasks = [client.get("/health") for _ in range(20)]
                results = await asyncio.gather(*tasks)
                
                # Wszystkie powinny się udać
                for response in results:
                    assert response.status_code == 200
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_stream_performance_under_load(self):
        """Test: Stream działa wydajnie pod obciążeniem"""
        from unittest.mock import AsyncMock, patch
        import time
        
        async def mock_stream():
            for i in range(10):
                yield b'frame_data'
                await asyncio.sleep(0.01)  # Symuluj 100 FPS
        
        with patch('app.api.routes.camera_service') as mock:
            mock.get_stream = mock_stream
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                start = time.time()
                
                async with client.stream("GET", "/stream") as response:
                    chunks = []
                    async for chunk in response.aiter_bytes():
                        chunks.append(chunk)
                        if len(chunks) >= 10:
                            break
                
                duration = time.time() - start
                
                # Powinno zająć mniej niż 200ms (10 klatek * 10ms + overhead)
                assert duration < 0.5
                assert len(chunks) == 10


def pytest_configure(config):
    """Dodaj custom markery"""
    config.addinivalue_line("markers", "integration: testy integracyjne z prawdziwym camera-server")
    config.addinivalue_line("markers", "slow: wolne testy (obciążeniowe)")


def pytest_addoption(parser):
    """Dodaj opcję --run-integration"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Uruchom testy integracyjne (wymagają działającego camera-server)"
    )
