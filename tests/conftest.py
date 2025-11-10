"""
Konfiguracja pytest dla testów produkcyjnych
"""
import pytest
import sys
import os
from pathlib import Path

# Dodaj katalog główny do PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


@pytest.fixture(scope="session")
def anyio_backend():
    """Konfiguracja backend dla asyncio"""
    return "asyncio"


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Konfiguracja zmiennych środowiskowych dla testów"""
    monkeypatch.setenv("CAMERA_SERVER_URL", "http://test-camera:8001")
    monkeypatch.setenv("APP_TITLE", "Test Welding Vision API")
    monkeypatch.setenv("DEBUG", "False")


@pytest.fixture
def sample_mjpeg_frame():
    """Fixture: Przykładowa klatka MJPEG"""
    return (
        b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n'
        b'\xff\xd8\xff\xe0\x00\x10JFIF'  # Fake JPEG header
        b'\r\n'
    )


@pytest.fixture
def healthy_camera_response():
    """Fixture: Odpowiedź healthy z camera-server"""
    return {
        "camera_ready": True,
        "camera_index": 1,
        "status": "healthy"
    }


@pytest.fixture
def unhealthy_camera_response():
    """Fixture: Odpowiedź unhealthy z camera-server"""
    return {
        "camera_ready": False,
        "camera_index": 1,
        "status": "unhealthy",
        "error": "Camera not accessible"
    }
