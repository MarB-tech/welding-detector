"""Tests for config/settings.py - application configuration."""

import pytest
from app.config.settings import Settings


class TestSettings:
    """Test application settings."""
    
    @pytest.mark.unit
    def test_default_settings(self):
        settings = Settings()
        assert settings.APP_HOST == "0.0.0.0"
        assert settings.APP_PORT == 8000
        assert isinstance(settings.DEBUG, bool)
    
    @pytest.mark.unit
    def test_app_metadata(self):
        settings = Settings()
        assert settings.APP_TITLE == "Welding Detector API"
        assert len(settings.APP_VERSION) > 0


