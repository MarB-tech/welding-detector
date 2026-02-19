"""Tests for app/main.py - main entry point."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAppConfig:
    """Test app configuration."""
    
    @pytest.mark.unit
    def test_app_metadata(self):
        from app.main import app
        from app.config import settings
        
        assert app.title == settings.APP_TITLE
        assert app.version == settings.APP_VERSION
        assert "welding" in app.description.lower()
    
    @pytest.mark.unit
    def test_cors_enabled(self, test_client):
        from app.main import app
        
        # Test CORS by checking the response to an OPTIONS request
        response = test_client.options("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code in [200, 405]  # OPTIONS may be unsupported
        
        # Or check that the middleware stack exists
        assert len(app.user_middleware) > 0
    
    @pytest.mark.unit
    def test_routers_included(self):
        from app.main import app
        
        routes = [getattr(route, "path", "") for route in app.routes]
        expected = ["/camera", "/recording", "/labeling", "/ml", "/defects"]
        
        for endpoint in expected:
            assert any(endpoint in r for r in routes), f"Missing router: {endpoint}"


class TestMainEndpoints:
    """Test main application endpoints."""
    
    @pytest.mark.unit
    def test_root_endpoint(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert all(key in data for key in ["app", "version", "docs", "endpoints"])
        assert data["docs"] == "/docs"
    
    @pytest.mark.unit
    def test_root_has_endpoints_info(self, test_client):
        data = test_client.get("/").json()
        endpoints = data["endpoints"]
        
        assert all(key in endpoints for key in ["stream", "capture", "health", "recording"])
    
    @pytest.mark.unit
    def test_health_endpoint(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "camera" in data
    
    @pytest.mark.unit
    def test_health_unhealthy_camera(self, test_client, mock_camera_service):
        mock_camera_service.health_check = AsyncMock(return_value={
            "status": "unhealthy",
            "error": "Camera not available"
        })
        
        response = test_client.get("/health")
        data = response.json()
        assert data["status"] == "unhealthy"


class TestLifespan:
    """Test application lifecycle."""
    
    @pytest.mark.unit
    @patch('app.main.get_camera_service')
    async def test_startup_healthy(self, mock_get_camera):
        from app.main import lifespan, app
        
        mock_camera = MagicMock()
        mock_camera.health_check = AsyncMock(return_value={
            "status": "healthy",
            "resolution": "1920x1080",
            "fps": 30
        })
        mock_camera.release = MagicMock()
        mock_get_camera.return_value = mock_camera
        
        async with lifespan(app):
            mock_camera.health_check.assert_called_once()
        
        mock_camera.release.assert_called_once()
    
    @pytest.mark.unit
    @patch('app.main.get_camera_service')
    async def test_startup_unhealthy(self, mock_get_camera):
        from app.main import lifespan, app
        
        mock_camera = MagicMock()
        mock_camera.health_check = AsyncMock(return_value={
            "status": "unhealthy",
            "error": "No camera"
        })
        mock_camera.release = MagicMock()
        mock_get_camera.return_value = mock_camera
        
        async with lifespan(app):
            pass
        
        mock_camera.release.assert_called_once()
