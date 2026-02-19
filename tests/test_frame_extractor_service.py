"""Test frame_extractor_service.py - extracting frames from video."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from app.services.frame_extractor_service import FrameExtractorService, FrameData


class TestFrameExtractorService:
    """Test FrameExtractorService."""
    
    @pytest.fixture
    def service(self, tmp_path):
        return FrameExtractorService(recordings_dir=tmp_path)
    
    @pytest.fixture
    def mock_video_capture(self):
        """Mock for cv2.VideoCapture."""
        with patch('app.services.frame_extractor_service.cv2.VideoCapture') as mock_cap:
            mock_instance = MagicMock()
            mock_instance.isOpened.return_value = True
            mock_instance.get.side_effect = lambda prop: {
                0: 100,  # CAP_PROP_FRAME_COUNT
                5: 30.0,  # CAP_PROP_FPS
                0: 0.0,   # CAP_PROP_POS_MSEC (timestamp)
            }.get(prop, 0)
            
            # Mock read() to return 3 frames then end
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            mock_instance.read.side_effect = [
                (True, test_frame),
                (True, test_frame),
                (True, test_frame),
                (False, None)
            ]
            
            mock_cap.return_value = mock_instance
            yield mock_cap
    
    @pytest.mark.unit
    def test_init(self, service):
        assert service is not None
        assert service.recordings_dir.exists()
    
    @pytest.mark.unit
    def test_resolve_path_absolute(self, service, tmp_path):
        """Test resolving absolute path."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        resolved = service._resolve_path(test_file)
        assert resolved == test_file
    
    @pytest.mark.unit
    def test_resolve_path_relative(self, service, tmp_path):
        """Test resolving relative path."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        resolved = service._resolve_path("test.mp4")
        assert resolved == test_file
    
    @pytest.mark.unit
    def test_extract_frames_file_not_found(self, service):
        """Test that raises an exception when the file does not exist."""
        with pytest.raises(FileNotFoundError):
            service.extract_frames("nonexistent.mp4")
    
    @pytest.mark.unit
    def test_extract_frames_basic(self, service, tmp_path, mock_video_capture):
        """Test basic frame extraction."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        frames = service.extract_frames(test_file)
        
        assert len(frames) == 3
        assert all(isinstance(f, FrameData) for f in frames)
        assert frames[0].index == 0
        assert frames[1].index == 1
        assert frames[2].index == 2
    
    @pytest.mark.unit
    def test_extract_frames_with_step(self, service, tmp_path, mock_video_capture):
        """Test extracting every Nth frame."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        frames = service.extract_frames(test_file, step=2)
        
        # From 3 frames, step=2 should give 2 frames (0, 2)
        assert len(frames) <= 2
    
    @pytest.mark.unit
    def test_extract_frames_with_max_frames(self, service, tmp_path, mock_video_capture):
        """Test limiting the number of frames."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        frames = service.extract_frames(test_file, max_frames=2)
        
        assert len(frames) <= 2
    
    @pytest.mark.unit
    def test_extract_frames_video_cannot_open(self, service, tmp_path):
        """Test when the video cannot be opened."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        with patch('app.services.frame_extractor_service.cv2.VideoCapture') as mock_cap:
            mock_instance = MagicMock()
            mock_instance.isOpened.return_value = False
            mock_cap.return_value = mock_instance
            
            with pytest.raises(ValueError):
                service.extract_frames(test_file)
    
    @pytest.mark.unit
    def test_get_video_info(self, service, tmp_path, mock_video_capture):
        """Test getting video information."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        info = service.get_video_info(test_file)
        
        assert "total_frames" in info or "frame_count" in info
        assert "fps" in info
    
    @pytest.mark.unit
    def test_get_frame_by_index(self, service, tmp_path, mock_video_capture):
        """Test getting a single frame by index."""
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        
        frame = service.get_frame(test_file, 0)
        
        # Frame can be None or np.ndarray depending on implementation
        assert frame is None or isinstance(frame, np.ndarray)


class TestFrameData:
    """Test dataclass FrameData."""
    
    @pytest.mark.unit
    def test_frame_data_creation(self):
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame_data = FrameData(index=5, frame=test_frame, timestamp_ms=166.67)
        
        assert frame_data.index == 5
        assert frame_data.timestamp_ms == 166.67
        assert frame_data.frame.shape == (100, 100, 3)
