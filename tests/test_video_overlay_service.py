"""Tests for VideoOverlayService - video annotation testing."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import numpy as np


@pytest.mark.unit
class TestVideoOverlayService:
    """Test VideoOverlayService with mocked dependencies."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create VideoOverlayService instance."""
        from app.services.video_overlay_service import VideoOverlayService
        from pathlib import Path
        service = VideoOverlayService(Path(tmp_path))
        return service

    def test_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert hasattr(service, 'recordings_dir')

    def test_process_video(self, service, tmp_path):
        """Test process_video method."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        with patch('cv2.VideoCapture') as mock_cap_class, \
             patch('cv2.VideoWriter') as mock_writer_class:
            
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                5: 30.0,  # FPS
                3: 640.0,  # Width
                4: 480.0,  # Height
                7: 100.0,  # Frame count
            }.get(prop, 0.0)
            mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
            mock_cap.release.return_value = None
            mock_cap_class.return_value = mock_cap
            
            mock_writer = Mock()
            mock_writer.isOpened.return_value = True
            mock_writer.write.return_value = None
            mock_writer.release.return_value = None
            mock_writer_class.return_value = mock_writer
            
            # Call process_video (runs in background thread)
            result = service.process_video("test.mp4")
            
            # Result should indicate whether processing started
            assert isinstance(result, bool)

    def test_process_video_file_not_found(self, service):
        """Test process_video with non-existent file."""
        result = service.process_video("nonexistent.mp4")
        
        # Should return False for non-existent file
        assert result is False

    def test_get_status(self, service, tmp_path):
        """Test get_status method."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        # Get status for non-existent processing
        status = service.get_status("test.mp4")
        assert status is None

    def test_get_all_status(self, service):
        """Test get_all_status method."""
        statuses = service.get_all_status()
        
        assert isinstance(statuses, dict)
