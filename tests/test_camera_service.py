"""Tests for CameraService - basic functionality with mocked cv2."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import numpy as np


@pytest.mark.unit
class TestCameraService:
    """Test CameraService with mocked OpenCV."""

    @pytest.fixture
    def mock_cv2_videocapture(self):
        """Mock cv2.VideoCapture."""
        with patch('cv2.VideoCapture') as mock_cap_class:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                3: 1920.0,  # CAP_PROP_FRAME_WIDTH
                4: 1080.0,  # CAP_PROP_FRAME_HEIGHT
                5: 30.0,    # CAP_PROP_FPS
            }.get(prop, 0.0)
            mock_cap.read.return_value = (True, np.zeros((1080, 1920, 3), dtype=np.uint8))
            mock_cap.release.return_value = None
            mock_cap_class.return_value = mock_cap
            yield mock_cap_class, mock_cap

    @pytest.fixture
    def service(self, mock_cv2_videocapture, tmp_path):
        """Create CameraService with mocked cv2."""
        from app.services.camera_service import CameraService
        
        service = CameraService(camera_index=0)
        service._running = False  # Don't start capture thread
        # Override recordings_dir after creation
        service.recordings_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)
        yield service
        service._running = False

    def test_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.camera_index == 0
        assert service.recordings_dir.exists()

    def test_get_frame(self, service):
        """Test get_frame returns frame data."""
        # Simulate frame in buffer
        fake_frame = b'\xff\xd8\xff\xe0fake jpeg data'
        service._last_frame = fake_frame
        
        result = service.get_frame()
        assert result == fake_frame

    def test_list_recordings(self, service, tmp_path):
        """Test list_recordings returns files."""
        # Create fake recordings
        service.recordings_dir = tmp_path
        (tmp_path / "rec1.mp4").write_bytes(b"fake1")
        (tmp_path / "rec2.mp4").write_bytes(b"fake2")
        
        recordings = service.list_recordings()
        
        assert len(recordings) >= 2
        assert any(r["filename"] == "rec1.mp4" for r in recordings)

    def test_get_recording_path(self, service, tmp_path):
        """Test get_recording_path."""
        service.recordings_dir = tmp_path
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"data")
        
        path = service.get_recording_path("test.mp4")
        
        assert path == test_file

    def test_delete_recording(self, service, tmp_path):
        """Test delete_recording."""
        service.recordings_dir = tmp_path
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"data")
        
        result = service.delete_recording("test.mp4")
        
        assert result is True
        assert not test_file.exists()

    def test_is_recording_property(self, service):
        """Test is_recording property."""
        service._recording = False
        assert service.is_recording is False
        
        service._recording = True
        assert service.is_recording is True

    def test_get_recording_duration(self, service):
        """Test get_recording_duration."""
        import time
        service._recording = True
        service._recording_start = time.perf_counter() - 5.0
        
        duration = service.get_recording_duration()
        assert duration >= 4.9 and duration <= 5.5
