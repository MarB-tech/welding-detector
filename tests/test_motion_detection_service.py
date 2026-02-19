"""Tests for MotionDetectionService - basic functionality with mocked cv2."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import numpy as np
import cv2


@pytest.mark.unit
class TestMotionDetectionService:
    """Test MotionDetectionService with mocked OpenCV."""

    @pytest.fixture
    def service(self):
        """Create MkService instance."""
        from app.services.motion_detection_service import MotionDetectionService
        return MotionDetectionService()

    def test_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert hasattr(service, 'threshold')

    def test_detect_motion_file_not_found(self, service):
        """Test detect_motion with non-existent file."""
        with pytest.raises(ValueError):
            service.detect_motion("nonexistent.mp4")

    def test_detect_motion_basic(self, service, tmp_path):
        """Test detect_motion with mocked video."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        with patch('cv2.VideoCapture') as mock_cap_class:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FRAME_COUNT: 100.0,
                cv2.CAP_PROP_FPS: 30.0,
            }.get(prop, 0.0)
            
            # Return sequence of frames
            frames = [
                (True, np.zeros((480, 640, 3), dtype=np.uint8)),  # Black frame
                (True, np.ones((480, 640, 3), dtype=np.uint8) * 255),  # White frame (motion)
                (False, None)  # End of video
            ]
            mock_cap.read.side_effect = frames
            mock_cap.release.return_value = None
            mock_cap_class.return_value = mock_cap
            
            with patch('cv2.cvtColor', side_effect=lambda x, _: x[:,:,0] if x is not None else None), \
                 patch('cv2.GaussianBlur', side_effect=lambda x, *args, **kwargs: x), \
                 patch('cv2.absdiff', return_value=np.zeros((480, 640), dtype=np.uint8)), \
                 patch('cv2.threshold', return_value=(0, np.zeros((480, 640), dtype=np.uint8))), \
                 patch('cv2.countNonZero', return_value=0):
                
                result = service.detect_motion(str(test_video))
            
            assert result is not None
            assert result.total_frames == 100
            assert result.fps == 30.0

    def test_trim_to_motion_no_segments(self, service, tmp_path):
        """Test trim_to_motion when no motion detected."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        with patch.object(service, 'detect_motion') as mock_detect:
            from app.services.motion_detection_service import MotionAnalysisResult
            mock_detect.return_value = MotionAnalysisResult(
                filename="test.mp4",
                total_frames=100,
                fps=30.0,
                duration_seconds=3.33,
                segments=[],
                motion_percentage=0.0
            )
            
            result = service.trim_to_motion(str(test_video))
            
            assert result["status"] == "no_motion"

    def test_detect_welding_process_not_found(self, service, tmp_path):
        """Test detect_welding_process when no welding detected."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        with patch('cv2.VideoCapture') as mock_cap_class:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FRAME_COUNT: 100.0,
                cv2.CAP_PROP_FPS: 30.0,
            }.get(prop, 0.0)
            
            # Return dark frames (no welding)
            frames = [(True, np.zeros((480, 640, 3), dtype=np.uint8))] * 5 + [(False, None)]
            mock_cap.read.side_effect = frames
            mock_cap.release.return_value = None
            mock_cap_class.return_value = mock_cap
            
            with patch('cv2.cvtColor', side_effect=lambda x, _: x[:,:,0] if x is not None else None), \
                 patch('numpy.mean', return_value=50.0):  # Dark frame, below threshold
                
                start, end = service.detect_welding_process(str(test_video))
                
                assert start is None
                assert end is None
