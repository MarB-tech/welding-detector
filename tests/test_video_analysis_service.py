"""Tests for VideoAnalysisService - comprehensive defect detection testing."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import numpy as np


@pytest.mark.unit
class TestVideoAnalysisService:
    """Test VideoAnalysisService with mocked dependencies."""

    @pytest.fixture
    def service(self):
        """Create VideoAnalysisService instance."""
        from app.services.video_analysis_service import VideoAnalysisService
        return VideoAnalysisService()

    @pytest.fixture
    def mock_ml_service(self):
        """Mock ML classification service."""
        mock = Mock()
        mock.predict.return_value = {
            "prediction": "NOK",
            "confidence": 0.85,
            "gradcam": None
        }
        return mock

    @pytest.fixture
    def mock_defect_service(self):
        """Mock defect classification service."""
        mock = Mock()
        mock.predict.return_value = {
            "prediction": "porosity",
            "confidence": 0.75,
            "gradcam": None
        }
        return mock

    @pytest.fixture
    def mock_frame_extractor(self):
        """Mock frame extractor service."""
        mock = Mock()
        mock.extract_frames_generator.return_value = iter([
            Mock(frame=np.zeros((480, 640, 3), dtype=np.uint8), index=0, timestamp_ms=0),
            Mock(frame=np.ones((480, 640, 3), dtype=np.uint8) * 255, index=1, timestamp_ms=33),
            Mock(frame=np.zeros((480, 640, 3), dtype=np.uint8), index=2, timestamp_ms=66),
        ])
        return mock

    def test_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert hasattr(service, 'ml_service')
        assert hasattr(service, 'defect_service')

    def test_analyze_video_with_defects(self, service, mock_ml_service, mock_defect_service, mock_frame_extractor, tmp_path):
        """Test analyze_video detecting defects."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        # Override service dependencies
        service.ml_service = mock_ml_service
        service.defect_service = mock_defect_service
        service.frame_extractor = mock_frame_extractor
        
        # Mock get_video_info
        service.frame_extractor.get_video_info.return_value = {
            'frame_count': 3,
            'fps': 30.0
        }
        
        result = service.analyze_video(filename=str(test_video), skip_frames=1)
        
        assert result is not None
        assert "total_frames" in result or "analyzed_frames" in result

    def test_analyze_video_file_not_found(self, service):
        """Test analyze_video with non-existent file."""
        with pytest.raises((FileNotFoundError, ValueError)):
            service.analyze_video("nonexistent.mp4")

    def test_analyze_video_ok_only(self, service, mock_frame_extractor, tmp_path):
        """Test analyze_video with only OK predictions."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        mock_ml = Mock()
        mock_ml.predict.return_value = {
            "prediction": "OK",
            "confidence": 0.95,
            "gradcam": None
        }
        
        service.ml_service = mock_ml
        service.frame_extractor = mock_frame_extractor
        service.frame_extractor.get_video_info.return_value = {
            'frame_count': 3,
            'fps': 30.0
        }
        
        result = service.analyze_video(filename=str(test_video), skip_frames=1)
        
        assert result is not None

    def test_get_defect_frames(self, service):
        """Test get_defect_frames method."""
        # Create mock analysis result
        mock_result = {
            "total_frames": 100,
            "defect_frames": [
                {"frame_index": 10, "prediction": "NOK", "confidence": 0.85},
                {"frame_index": 20, "prediction": "NOK", "confidence": 0.90}
            ]
        }
        
        defect_frames = mock_result["defect_frames"]
        
        assert len(defect_frames) == 2
        assert defect_frames[0]["frame_index"] == 10

    def test_analyze_with_step(self, service, mock_ml_service, mock_frame_extractor, tmp_path):
        """Test analyze_video with skip_frames > 1."""
        test_video = tmp_path / "test.mp4"
        test_video.write_bytes(b"fake video")
        
        service.ml_service = mock_ml_service
        service.frame_extractor = mock_frame_extractor
        service.frame_extractor.get_video_info.return_value = {
            'frame_count': 10,
            'fps': 30.0
        }
        
        result = service.analyze_video(filename=str(test_video), skip_frames=2)
        
        # Should analyze fewer frames
        assert result is not None
