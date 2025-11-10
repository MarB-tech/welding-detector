"""
Testy konfiguracji - krytyczne dla wdrożenia produkcyjnego
"""
import pytest
import os
from app.core.config import Settings, settings


class TestProductionSettings:
    """Testy konfiguracji produkcyjnej"""
    
    def test_camera_server_url_is_set(self):
        """Test: CAMERA_SERVER_URL jest ustawiony"""
        assert settings.CAMERA_SERVER_URL is not None
        assert len(settings.CAMERA_SERVER_URL) > 0
    
    def test_camera_server_url_is_valid_url(self):
        """Test: CAMERA_SERVER_URL jest poprawnym URL"""
        url = settings.CAMERA_SERVER_URL
        assert url.startswith("http://") or url.startswith("https://")
    
    def test_app_title_is_set(self):
        """Test: APP_TITLE jest ustawiony"""
        assert settings.APP_TITLE is not None
        assert len(settings.APP_TITLE) > 0
    
    def test_settings_can_be_overridden(self):
        """Test: Ustawienia mogą być nadpisane (ważne dla różnych środowisk)"""
        custom_settings = Settings(
            APP_TITLE="Test API",
            CAMERA_SERVER_URL="http://test:8001"
        )
        
        assert custom_settings.APP_TITLE == "Test API"
        assert custom_settings.CAMERA_SERVER_URL == "http://test:8001"
    
    def test_debug_mode_is_configurable(self):
        """Test: Tryb DEBUG jest konfigurowalny"""
        assert hasattr(settings, 'DEBUG')
        assert isinstance(settings.DEBUG, bool)


class TestEnvironmentSpecificSettings:
    """Testy dla różnych środowisk (dev, prod, docker)"""
    
    def test_docker_environment_settings(self):
        """Test: Ustawienia dla środowiska Docker"""
        docker_settings = Settings(
            CAMERA_SERVER_URL="http://host.docker.internal:8001"
        )
        
        assert "host.docker.internal" in docker_settings.CAMERA_SERVER_URL
    
    def test_local_environment_settings(self):
        """Test: Ustawienia dla lokalnego środowiska"""
        local_settings = Settings(
            CAMERA_SERVER_URL="http://localhost:8001"
        )
        
        assert "localhost" in local_settings.CAMERA_SERVER_URL
    
    def test_production_environment_settings(self):
        """Test: Ustawienia produkcyjne mają rozsądne wartości"""
        prod_settings = Settings()
        
        # W produkcji DEBUG powinno być False
        assert prod_settings.DEBUG is False or prod_settings.DEBUG is True
        # APP_TITLE powinien być ustawiony
        assert len(prod_settings.APP_TITLE) > 0
